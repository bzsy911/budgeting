import pandas as pd
import datetime
from source.utils import Map


class PricingAnalysisCollector:

    def __init__(self, excel, name):
        self.name = name
        self.raw_df = pd.read_excel(excel, sheet_name=name)
        self.map = Map(self.raw_df)
        self.pricing = self._process()

    def _process(self):
        res = {
            'Scenario': self.name,
            'Total Fees Discounted': self._total_fees_discounted(),
            'Remaining Fee including Gignow': self._remaining_fee_including_gignow(),
            'Margin (%) with Gignow': self._margin_pct_with_gignow(),
            'Team': self._team(),
            'Activity Code': self.map.get_values_below('Activity Code'),
            'All Fees Discounted': self.map.get_values_below('Total Fees Discounted')
        }
        return res

    def _total_fees_discounted(self):
        return self.map.get_value_by_intersection('Total', 'Total Fees Discounted')

    def _remaining_fee_including_gignow(self):
        return self.map.get_value_by_direction('Remaining fee including Gignow', 0, (0, 1))

    def _margin_pct_with_gignow(self):
        return self.map.get_value_by_direction('Margin (%) with Gignow', 1, (0,1))

    def _team(self):
        names = self.map.get_values_below('Name')  # [[name, (i, j)], [], ...]
        features = ['Level', 'Activity Code', 'Discounted Rate', 'Base Cost', 'Start Date', 'End Date',
                    'Total Fees Discounted', 'Hours']
        columns = [j for f in features for _, j in self.map.finder[f]]
        return [[name] + list(map(lambda j: self.map.loc[(coord[0], j)], columns)) for name, coord in names]


class BurnChartCollector:
    """
    The collector of the newest budget and actual data for the burn chart
    Essential anchors:
        Burn Chart Tab:
            - this tab has no header (dates are on row 1)
            - 'Total Budgeted Cost - Extension' is used to locate budget fees
            - 'Total Actual Cost' is used to locate actual fees
            - 'Headcount' is used to located the 2 output table for accumulation
        Bill Tab:
            - the 2nd 'Bill Rate' is used to locate both bill rate and hours
    """

    def __init__(self, excel, burn_chart_tab, bill_tab, the_friday):
        self.bill_map = Map(pd.read_excel(excel, sheet_name=bill_tab))
        self.burn_chart_map = Map(pd.read_excel(excel, sheet_name=burn_chart_tab, header=None))
        self.the_friday = the_friday
        self.budget_actual = self._process()

    def _process(self):
        res = {
            'Headers': self._get_headers(),
            'Budget Fees': self._get_budget_fees(),
            'Actual Fees': self._get_actual_fees(),
            'Bill Rate and Hours': self._get_bill_rate_and_hours()
        }
        return res

    def _get_headers(self):
        r, c = self.burn_chart_map.find(pd._libs.tslibs.timestamps.Timestamp(self.the_friday))
        week = self.burn_chart_map.loc[(r+1, c)]

        def format_header(i):
            wk = int(week[-2:]) - i
            month = f"{(self.the_friday - datetime.timedelta(7*i)).strftime('%B')[:3]}"
            day = f"{(self.the_friday - datetime.timedelta(7*i)).strftime('%d')}"
            return f"Week {wk} ({month} - {day})"

        return [format_header(i) for i in range(int(week[-2:]))][::-1]

    def _get_budget_fees(self):
        r, c_0 = self.burn_chart_map.find('Total Budgeted Cost - Extension')
        _, c_t = self.burn_chart_map.find(pd._libs.tslibs.timestamps.Timestamp(self.the_friday))
        return [[self.burn_chart_map.loc[(i, j)] for i in range(r+3, r+11)] for j in range(c_0+2, c_t+1)]

    def _get_actual_fees(self):
        r, c_0 = self.burn_chart_map.find('Total Actual Cost')
        _, c_t = self.burn_chart_map.find(pd._libs.tslibs.timestamps.Timestamp(self.the_friday))
        return [[self.burn_chart_map.loc[(i, j)] for i in range(r+3, r+11)] for j in range(c_0+2, c_t+1)]

    def _get_bill_rate_and_hours(self):
        bill_rate = self.bill_map.get_consecutive_value_below('Bill Rate', 1)
        _, c = [d for d in self.bill_map.finder[pd._libs.tslibs.timestamps.Timestamp(self.the_friday)]
                if d[0] == bill_rate[0][1][0]-2][0]
        hours = [[x if x > 0 else 0 for x in [self.bill_map.loc[(i, j)]
                                              for i in [p[1][0] for p in bill_rate]]]
                 for j in range(c-(self.the_friday-datetime.date(2020, 3, 6)).days//7, c+1)]
        return bill_rate, hours

    def _get_prev_cumulative(self):
        rows = [range(i+1, i+9) for i, _ in self.burn_chart_map.finder['Headcount']]
        cols = [self.burn_chart_map.find('Headcount')[1] + j + 1 for j in range(int(self._get_headers()[-1].split()[1])*2-2)]
        cum_1_budget = [sum([self.burn_chart_map.loc[(i, j)] for j in cols[::2]]) for i in rows[0]]
        cum_1_actual = [sum([self.burn_chart_map.loc[(i, j)] for j in cols[1::2]]) for i in rows[0]]
        cum_2_budget = [sum([self.burn_chart_map.loc[(i, j)] for j in cols[::2]]) for i in rows[1]]
        cum_2_actual = [sum([self.burn_chart_map.loc[(i, j)] for j in cols[1::2]]) for i in rows[1]]
        return cum_1_budget, cum_1_actual, cum_2_budget, cum_2_actual
