import pandas as pd
from source.base import CitiBudgeting
from source.collectors import PricingAnalysisCollector

pd.set_option('display.max_columns', None, 'display.expand_frame_repr', False)


class PricingAnalysis(CitiBudgeting):

    def __init__(self, excel, tab_1='Gignow', tab_2='Tech'):
        super().__init__(excel)
        self.name = 'pricing analysis'
        self.tab_1 = PricingAnalysisCollector(self.excel, tab_1)
        self.tab_2 = PricingAnalysisCollector(self.excel, tab_2)
        self.functions = [self._total_impact,
                          self._change_log,
                          self._impact_by_activity_code]

    def run_report(self, save=True):
        super().run_report_txt(self.functions, save)

    # ---------- App Functions ----------
    def _total_impact(self):
        columns = ['Scenario', 'Total Fees Discounted', 'Remaining Fee including Gignow', 'Margin (%) with Gignow']
        scenario_1 = list(map(lambda x: self.tab_1.pricing[x], columns))
        scenario_2 = list(map(lambda x: self.tab_2.pricing[x], columns))
        return f"""
1. Total Impact for Project:
{pd.DataFrame([scenario_1, scenario_2], columns=columns)}
"""

    def _change_log(self):
        columns = ['Name', 'Level', 'Activity Code', 'Discounted Rate', 'Base Cost', 'Date_Gignow', 'Date_Tech',
                   'Hours_Gignow', 'Hours_Tech', 'Delta_Fees']
        team_1 = self.tab_1.pricing['Team']
        team_2 = self.tab_2.pricing['Team']

        def log_1():
            guys = [x for x in team_2 if x[0] not in [y[0] for y in team_1]]
            res = [ls[:5] + ['N/A', f'{str(ls[5])[:10]} - {str(ls[6])[:10]}', 'N/A',
                             ' '.join(sorted([str(x) for x in set(ls[8:]) if x > 0])), ls[7]] for ls in guys]
            return pd.DataFrame(res, columns=columns)

        def log_2():
            guys = [(y, x) for x in team_2 for y in team_1 if x[0] == y[0] and x[2] == y[2] and
                    any([a-b for a, b in zip([a if a > 0 else 0 for a in x[8:]], [b if b > 0 else 0 for b in y[8:]])])]
            res = [t[:5] + [f'{str(g[5])[:10]} - {str(g[6])[:10]}',
                            f'{str(t[5])[:10]} - {str(t[6])[:10]}',
                            ' '.join(sorted([str(x) for x in set(g[8:]) if x > 0])),
                            ' '.join(sorted([str(x) for x in set(t[8:]) if x > 0])),
                            t[7] - g[7]] for g, t in guys]
            return pd.DataFrame(res, columns=columns)

        def log_3():
            guys = set()
            res = []
            for x in team_2:
                for y in team_1:
                    if x[0] == y[0] and x[2] != y[2]:  # get a different code!
                        # check if this guy is already addressed
                        if x[0] in guys:
                            continue
                        else:  # collect all info about this guy
                            guys.add(x[0])
                            after = [n for n in team_2 if n[0] == x[0]]
                            before = [m for m in team_1 if m[0] == x[0]]
                            codes = set([n[2] for n in after] + [m[2] for m in before])
                            items = []
                            for code in codes:
                                # if same hours then don't show
                                if any([n[2] == code for n in after]) and not any([m[2] == code for m in before]):
                                    ls = [n for n in after if n[2] == code][0]
                                    if ls[7] != 0:
                                        items.append(ls[:5] +
                                                     ['N/A', f'{str(ls[5])[:10]} - {str(ls[6])[:10]}',
                                                      'N/A', ' '.join(sorted([str(x) for x in set(ls[8:]) if x > 0])),
                                                      ls[7]])
                                elif not any([n[2] == code for n in after]) and any([m[2] == code for m in before]):
                                    ls = [m for m in before if m[2] == code][0]
                                    if ls[7] != 0:
                                        items.append(ls[:5] +
                                                     [f'{str(ls[5])[:10]} - {str(ls[6])[:10]}', 'N/A',
                                                      ' '.join(sorted([str(x) for x in set(ls[8:]) if x > 0])), 'N/A',
                                                      ls[7]])
                                else:
                                    t = [n for n in after if n[2] == code][0]
                                    g = [m for m in before if m[2] == code][0]
                                    if t[7] != g[7]:
                                        items.append(t[:5] + [f'{str(g[5])[:10]} - {str(g[6])[:10]}',
                                                              f'{str(t[5])[:10]} - {str(t[6])[:10]}',
                                                              ' '.join(sorted([str(x) for x in set(g[8:]) if x > 0])),
                                                              ' '.join(sorted([str(x) for x in set(t[8:]) if x > 0])),
                                                              t[7] - g[7]])
                            if len(items) > 1:
                                res.extend(items)
            return pd.DataFrame(res, columns=columns)

        return f"""
2. Change Log:

2.1 Following are the new people added:
{log_1() if log_1().shape[0] else 'NO NEWLY ADDED PEOPLE!'}

2.2 Followings are the records who modify hours:
{log_2() if log_2().shape[0] else 'NO ONE MODIFIED HOURS!'}

2.3 Followings are the records who switch activity code:
{log_3() if log_3().shape[0] else 'NO ONE SWITCHED ACTIVITY CODE!'}
"""

    def _impact_by_activity_code(self):
        columns = ['Activity Code', self.tab_1.pricing['Scenario'], self.tab_2.pricing['Scenario']]

        def sum_up(codes, fees):
            df = pd.DataFrame([[c[0], f[0]] for c, f in zip(codes, fees)], columns=['Code', 'Fees'])
            df = df.groupby('Code').sum()
            return df

        g = sum_up(self.tab_1.pricing['Activity Code'], self.tab_1.pricing['All Fees Discounted']).reset_index()
        t = sum_up(self.tab_2.pricing['Activity Code'], self.tab_2.pricing['All Fees Discounted']).reset_index()
        res = g.merge(t, on='Code')

        res.columns = columns
        res['Fee Difference'] = res[columns[2]] - res[columns[1]]

        res['dummy'] = range(len(res))
        res.iloc[int(res[res['Activity Code'] == 'Total'].index.values), 4] = len(res)
        res = res.sort_values("dummy").reset_index(drop='True').drop('dummy', axis=1)
        return f"""
3.Impact by Activity Code:
{res}
"""


if __name__ == "__main__":
    jie = PricingAnalysis('Budget Tracker 0727.xlsx')
    jie.run_report()
