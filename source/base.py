class CitiBudgeting:

    def __init__(self, excel):
        self.input = 'input/'
        self.output = 'output/'
        self.time_exp = 'TimeExp/'
        self.excel = self.input + excel
        self.name = ''

    def run_report_txt(self, functions, save, prefix=''):
        res = '\n'.join([f() for f in functions])
        if prefix:
            res = prefix + res
        print(res)
        if save:
            file_name = f'{self.output}{self.name} {self.excel.split()[-1][:4]}.txt'
            with open(file_name, 'w+') as f:
                f.write(res)
            print(f'Result has been saved to {file_name}')
        return

    def run_report_excel(self, function, save):
        res = function()
        print(res)
        if save:
            file_name = f'{self.output}{self.name} {self.excel.split()[-1][:4]}.xlsx'
            res.to_excel(file_name)
            print(f'Result has been saved to {file_name}')
        return
