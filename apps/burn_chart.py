import pandas as pd
from datetime import date, timedelta
from source.base import CitiBudgeting
from source.collectors import BurnChartCollector
pd.set_option('display.max_columns', None, 'display.expand_frame_repr', False)


class BurnChart(CitiBudgeting):

    def __init__(self, excel, burn_chart_tab='Burn Chart', bill_tab='Bill', week=-1):
        super().__init__(excel)
        self.name = 'burn chart'
        self.app = BurnChartCollector(self.excel, burn_chart_tab, bill_tab,
                                      date.today() + timedelta(days=4-date.today().weekday(), weeks=week))
        self.function = self._weekly_chart

    def run_report(self, save=True):
        super().run_report_excel(self.function, save)

    # ---------- App Functions ----------
    def _weekly_chart(self):
        headers = self.app.budget_actual['Headers']
        headers = [
            [ele for t in zip(headers, [''] * len(headers)) for ele in t] + ['Cumulative', ''],
            ['Budgeted Fees', 'Actual Fees'] * (len(headers)+1)
        ]

        cum_bud = [sum(t) for t in zip(*self.app.budget_actual['Budget Fees'])]
        cum_act = [sum(t) for t in zip(*self.app.budget_actual['Actual Fees'])]
        cum_adj_act = [sum(t) for t in zip(*self._adjusted_actual())]

        numbers = [ele
                   for p in zip(self.app.budget_actual['Budget Fees'], self.app.budget_actual['Actual Fees'])
                   for ele in p]
        numbers = [list(t) for t in zip(*(numbers + [cum_bud] + [cum_act]))]

        numbers_adj = [ele
                       for p in zip(self.app.budget_actual['Budget Fees'], self._adjusted_actual())
                       for ele in p]
        numbers_adj = [list(t) for t in zip(*(numbers_adj + [cum_bud] + [cum_adj_act]))]

        return pd.DataFrame(headers + numbers + [['']*len(headers)] + headers + numbers_adj)

    # ---------- Helper Functions ----------
    def _adjusted_actual(self):
        def adjust(act, adj):
            res = [x for x in act]
            res[2] = adj
            res[0] = res[-1] - sum(res[1:-1])
            return res

        bill_rate, hours = self.app.budget_actual['Bill Rate and Hours']
        return [adjust(act, sum([r[0]*h for r, h in zip(bill_rate, hour)]))
                for act, hour in zip(self.app.budget_actual['Actual Fees'], hours)]


if __name__ == "__main__":
    jie = BurnChart('Budget Tracker 0727.xlsx')
    jie.run_report()

