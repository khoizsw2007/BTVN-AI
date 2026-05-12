"""
SQL query methods for RiskAnalysisFrame.
Mixed into RiskAnalysisFrame via inheritance.
"""
from datetime import datetime, timedelta

from data.uber import get_db_connection
from ._helpers import safe_float, sql_in, sql_literals
from ._helpers import STATUS_CANCEL_CUSTOMER, STATUS_CANCEL_DRIVER
from ._helpers import STATUS_INCOMPLETE, STATUS_COMPLETED


class RiskQueriesMixin:
    """SQL query methods — mixed into RiskAnalysisFrame."""

    def _query_one(self, query, params=None):
        conn = get_db_connection()
        if not conn:
            raise RuntimeError("Cannot connect to the configured SQL database.")
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(query, params or [])
            return cur.fetchone() or {}
        finally:
            conn.close()

    def _query_all(self, query, params=None):
        conn = get_db_connection()
        if not conn:
            raise RuntimeError("Cannot connect to the configured SQL database.")
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(query, params or [])
            return cur.fetchall()
        finally:
            conn.close()

    def _filter_snapshot(self):
        start_iso, end_iso = (self.date_picker.get_range_iso()
                              if self.date_picker else (None, None))
        return {
            "start": start_iso or self.default_start,
            "end": end_iso or self.default_end,
            "region": self.region_var.get(),
            "service": self.service_var.get(),
            "payment": self.payment_var.get(),
            "status": self.status_var.get(),
            "peak": self.peak_var.get(),
            "reason": self.selected_reason,
        }

    def _load_dashboard_data(self, snapshot):
        try:
            where, params = self._build_where(snapshot)
            prev_where, prev_params = self._build_previous_where(snapshot)
            data = {
                "kpi": self._query_kpis(where, params, prev_where, prev_params),
                "reasons": self._query_reasons(where, params),
                "vtat": self._query_vtat_analysis(where, params),
                "vehicles": self._query_vehicle_cancel_rates(where, params),
                "fraud": self._query_fraud(where, params),
                "drivers": self._query_driver_ranking(where, params),
            }
            self.after(0, lambda: self._render_dashboard(data))
        except Exception as exc:
            self.after(0, lambda: self._render_error(str(exc)))

    def _build_where(self, snapshot):
        clauses = ["1=1"]
        params = []
        if snapshot["start"] and snapshot["end"]:
            clauses.append("`Date` BETWEEN %s AND %s")
            params.extend([snapshot["start"], snapshot["end"]])
        if snapshot["region"] != "All":
            clauses.append("(`Pickup Location` = %s OR `Drop Location` = %s)")
            params.extend([snapshot["region"], snapshot["region"]])
        if snapshot["service"] != "All":
            clauses.append("`Vehicle Type` = %s")
            params.append(snapshot["service"])
        if snapshot["payment"] != "All":
            clauses.append("`Payment Method` = %s")
            params.append(snapshot["payment"])
        if snapshot["status"] != "All":
            clauses.append("`Booking Status` = %s")
            params.append(snapshot["status"])
        if snapshot["peak"]:
            clauses.append("HOUR(COALESCE(`Full_Timestamp`, CONCAT(`Date`, ' ', "
                           "`Time`))) IN (7,8,9,17,18,19,20)")
        if snapshot["reason"]:
            clauses.append("(`Reason for cancelling by Customer` = %s OR "
                           "`Driver Cancellation Reason` = %s)")
            params.extend([snapshot["reason"], snapshot["reason"]])
        return "WHERE " + " AND ".join(clauses), params

    def _build_previous_where(self, snapshot):
        try:
            start = datetime.strptime(snapshot["start"], "%Y-%m-%d")
            end = datetime.strptime(snapshot["end"], "%Y-%m-%d")
        except ValueError:
            return "WHERE 1=0", []
        days = max(1, (end - start).days + 1)
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days - 1)
        previous = dict(snapshot)
        previous["start"] = prev_start.strftime("%Y-%m-%d")
        previous["end"] = prev_end.strftime("%Y-%m-%d")
        where, params = self._build_where(previous)
        return where, params

    def _query_kpis(self, where, params, prev_where, prev_params):
        expr = self._kpi_expr()
        current = self._query_one(f"SELECT {expr} FROM rides {where}", params)
        previous = self._query_one(
            f"SELECT {expr} FROM rides {prev_where}", prev_params)
        return current, previous

    def _kpi_expr(self):
        return f"""
            COUNT(*) total,
            SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_CANCEL_CUSTOMER)}
                OR `Cancelled Rides by Customer` > 0 THEN 1 ELSE 0 END)
                customer_cancelled,
            SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_CANCEL_DRIVER)}
                OR `Cancelled Rides by Driver` > 0 THEN 1 ELSE 0 END)
                driver_cancelled,
            SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_INCOMPLETE)}
                OR `Incomplete Rides` > 0 THEN 1 ELSE 0 END) incomplete,
            SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_COMPLETED)}
                THEN 1 ELSE 0 END) completed
        """

    def _query_reasons(self, where, params):
        query = f"""
            SELECT reason,
                   SUM(customer_cnt) customer_cnt,
                   SUM(driver_cnt) driver_cnt,
                   SUM(customer_cnt + driver_cnt) total_cnt
            FROM (
                SELECT `Reason for cancelling by Customer` reason,
                       COUNT(*) customer_cnt, 0 driver_cnt
                FROM rides {where}
                  AND `Reason for cancelling by Customer`
                      NOT IN ('', 'None', 'Not Applicable', '0')
                GROUP BY `Reason for cancelling by Customer`
                UNION ALL
                SELECT `Driver Cancellation Reason` reason,
                       0 customer_cnt, COUNT(*) driver_cnt
                FROM rides {where}
                  AND `Driver Cancellation Reason`
                      NOT IN ('', 'None', 'Not Applicable', '0')
                GROUP BY `Driver Cancellation Reason`
            ) x
            GROUP BY reason
            ORDER BY total_cnt DESC
            LIMIT 30
        """
        return self._query_all(query, params + params)

    def _query_vtat_analysis(self, where, params):
        query = f"""
            SELECT
                   CASE
                       WHEN `Avg VTAT` < 3 THEN '0-3 min'
                       WHEN `Avg VTAT` < 6 THEN '3-6 min'
                       WHEN `Avg VTAT` < 9 THEN '6-9 min'
                       WHEN `Avg VTAT` < 12 THEN '9-12 min'
                       WHEN `Avg VTAT` < 15 THEN '12-15 min'
                       ELSE '15+ min'
                   END vtat_bucket,
                   CASE
                       WHEN `Avg VTAT` < 3 THEN 1
                       WHEN `Avg VTAT` < 6 THEN 2
                       WHEN `Avg VTAT` < 9 THEN 3
                       WHEN `Avg VTAT` < 12 THEN 4
                       WHEN `Avg VTAT` < 15 THEN 5
                       ELSE 6
                   END bucket_order,
                   COUNT(*) total,
                   SUM(CASE WHEN `Booking Status`
                       IN {sql_literals(STATUS_CANCEL_CUSTOMER)}
                       OR `Cancelled Rides by Customer` > 0 THEN 1 ELSE 0 END)
                       cancelled,
                   AVG(`Avg VTAT`) avg_vtat,
                   AVG(`Avg CTAT`) avg_ctat,
                   ROUND(SUM(CASE WHEN `Booking Status`
                       IN {sql_literals(STATUS_CANCEL_CUSTOMER)}
                       OR `Cancelled Rides by Customer` > 0 THEN 1 ELSE 0 END)
                       / COUNT(*) * 100, 2) cancel_rate
            FROM rides {where}
              AND `Avg VTAT` IS NOT NULL AND `Avg VTAT` >= 0
            GROUP BY vtat_bucket, bucket_order
            ORDER BY bucket_order
        """
        return self._query_all(query, params)

    def _query_vehicle_cancel_rates(self, where, params):
        combined = STATUS_CANCEL_CUSTOMER + STATUS_CANCEL_DRIVER
        query = f"""
            SELECT `Vehicle Type` vehicle_type,
                   COUNT(*) total_rides,
                   SUM(CASE WHEN `Booking Status` IN {sql_literals(combined)}
                       OR `Cancelled Rides by Customer` > 0
                       OR `Cancelled Rides by Driver` > 0 THEN 1 ELSE 0 END)
                       cancelled_rides,
                   ROUND(SUM(CASE WHEN `Booking Status` IN {sql_literals(combined)}
                       OR `Cancelled Rides by Customer` > 0
                       OR `Cancelled Rides by Driver` > 0 THEN 1 ELSE 0 END)
                       / COUNT(*) * 100, 2) cancel_rate,
                   AVG(NULLIF(`Driver Ratings`, 0)) avg_driver_rating
            FROM rides {where}
              AND `Vehicle Type` IS NOT NULL
              AND `Vehicle Type` NOT IN ('', 'None', 'NaN', '0')
            GROUP BY `Vehicle Type`
            HAVING total_rides >= 50 AND cancelled_rides > 0
            ORDER BY cancel_rate DESC, cancelled_rides DESC
            LIMIT 12
        """
        return self._query_all(query, params)

    def _query_fraud(self, where, params):
        suspicious_statuses = (
            "Cancelled", "Cancelled by Driver", "Cancelled by Customer",
            "Incomplete", "No Completed", "No Complete")
        query = f"""
            SELECT r.`Booking ID`, r.`Driver ID`,
                   COALESCE(r.`Driver ID`, 'Unknown') driver_name,
                   r.`Ride Distance`, r.`Booking Status`, r.`Payment Method`,
                   COALESCE(r.`Full_Timestamp`,
                       CONCAT(r.`Date`, ' ', r.`Time`)) event_time,
                   r.`Pickup Location` region,
                   driver_stats.suspicious_count,
                   (45
                    + CASE WHEN r.`Ride Distance` >= 12 THEN 25
                           WHEN r.`Ride Distance` >= 6 THEN 12 ELSE 5 END
                    + LEAST(driver_stats.suspicious_count * 6, 30)
                    + CASE WHEN r.`Booking Status`
                        IN ('Cancelled by Driver', 'Cancelled') THEN 10 ELSE 0 END
                   ) risk_score
            FROM rides r
            JOIN (
                SELECT `Driver ID`, COUNT(*) suspicious_count
                FROM rides
                WHERE `Payment Method`='Cash'
                  AND `Booking Status` IN {sql_in(suspicious_statuses)}
                  AND `Ride Distance` > 1.0
                GROUP BY `Driver ID`
            ) driver_stats ON driver_stats.`Driver ID` = r.`Driver ID`
            {self._alias_where(where, 'r')}
              AND r.`Payment Method`='Cash'
              AND r.`Booking Status` IN {sql_in(suspicious_statuses)}
              AND r.`Ride Distance` > 1.0
            ORDER BY risk_score DESC, r.`Ride Distance` DESC
            LIMIT 5000
        """
        return self._query_all(query,
                               list(suspicious_statuses) + params + list(
                                   suspicious_statuses))

    def _alias_where(self, where, alias):
        aliased = where
        for col in ["Date", "Pickup Location", "Drop Location", "Vehicle Type",
                    "Payment Method", "Booking Status", "Full_Timestamp", "Time",
                    "Reason for cancelling by Customer",
                    "Driver Cancellation Reason"]:
            aliased = aliased.replace(f"`{col}`", f"{alias}.`{col}`")
        return aliased

    def _query_driver_ranking(self, where, params):
        volume_row = self._query_one(f"""
            SELECT MAX(accepted_rides) max_rides
            FROM (
                SELECT COUNT(*) accepted_rides
                FROM rides {where}
                  AND `Driver ID` IS NOT NULL
                  AND `Driver ID` NOT IN ('', 'None', 'NaN', '0', 'Unassigned')
                GROUP BY `Driver ID`
            ) volume
        """, params)
        max_rides = int(volume_row.get("max_rides") or 0)
        threshold = 30 if max_rides >= 30 else max(2, min(5, max_rides))
        if max_rides < 2:
            return {"rows": [], "threshold": 30}
        query = f"""
            SELECT `Driver ID`,
                   COUNT(*) accepted_rides,
                   SUM(CASE WHEN `Booking Status`
                       IN {sql_literals(STATUS_CANCEL_DRIVER)}
                       OR `Cancelled Rides by Driver` > 0 THEN 1 ELSE 0 END)
                       driver_cancelled,
                   SUM(CASE WHEN `Booking Status`
                       IN {sql_literals(STATUS_CANCEL_CUSTOMER)}
                       OR `Cancelled Rides by Customer` > 0 THEN 1 ELSE 0 END)
                       customer_cancelled,
                   AVG(NULLIF(`Driver Ratings`, 0)) avg_rating,
                   ROUND(SUM(CASE WHEN `Booking Status`
                       IN {sql_literals(STATUS_CANCEL_DRIVER)}
                       OR `Cancelled Rides by Driver` > 0 THEN 1 ELSE 0 END)
                       / COUNT(*) * 100, 1) cancel_rate,
                   ROUND(SUM(CASE WHEN `Booking Status`
                       IN {sql_literals(STATUS_CANCEL_CUSTOMER)}
                       OR `Cancelled Rides by Customer` > 0 THEN 1 ELSE 0 END)
                       / COUNT(*) * 100, 1) customer_cancel_rate,
                   ROUND(SUM(CASE WHEN `Booking Status`
                       IN {sql_literals(STATUS_CANCEL_DRIVER + STATUS_CANCEL_CUSTOMER)}
                       OR `Cancelled Rides by Driver` > 0
                       OR `Cancelled Rides by Customer` > 0 THEN 1 ELSE 0 END)
                       / COUNT(*) * 100, 1) total_cancel_rate,
                   COALESCE(NULLIF(SUBSTRING_INDEX(
                       GROUP_CONCAT(NULLIF(`Driver Cancellation Reason`, '')
                           ORDER BY `Driver Cancellation Reason` SEPARATOR ','),
                       ',', 1), ''), 'Not Available') common_reason
            FROM rides {where}
              AND `Driver ID` IS NOT NULL
              AND `Driver ID` NOT IN ('', 'None', 'NaN', '0', 'Unassigned')
            GROUP BY `Driver ID`
            HAVING accepted_rides >= %s
               AND (driver_cancelled > 0 OR customer_cancelled > 0)
            ORDER BY total_cancel_rate DESC, driver_cancelled DESC,
                     customer_cancelled DESC
            LIMIT 2000
        """
        return {"rows": self._query_all(query, params + [threshold]),
                "threshold": threshold}
