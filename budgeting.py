from apps import Validator, PricingAnalysis, BurnChart


class MyBudget:

    def __init__(self):
        self.this_week = 'Budget Tracker 1005.xlsx'
        self.last_week = 'Budget Tracker 0824.xlsx'

    def run_validation(self):
        app = Validator(self.this_week)
        app.run_report()
        app.run_comparison(self.last_week)

    def run_pricing_analysis(self):
        app = PricingAnalysis(self.this_week)
        app.run_report()

    def run_burn_chart(self):
        app = BurnChart(self.this_week)
        app.run_report()

    def run(self):
        self.run_validation()
        self.run_pricing_analysis()
        self.run_burn_chart()


if __name__ == "__main__":
    my_budget = MyBudget()
    my_budget.run()
