from PyQt5.uic import loadUiType
import re

ui_data_editor, q_data_editor = loadUiType('ui/data_editor.ui')

class DataEditor(q_data_editor, ui_data_editor):

    def __init__(self, origin):
        super().__init__()
        self.setupUi(self)
        self.origin = origin
        self.init_slot()
        self.init_ui()
        self.command_index = 1

    def init_ui(self):
        self.text_pad.setReadOnly(1)
        self.text_pad.setFontFamily('courier')
        self.line_edit.clear()

    def init_slot(self):
        self.line_edit.returnPressed.connect(self.on_press_enter)

    def on_press_enter(self):
        color_exp = '#191919' # black
        color_err = '#ff0000'  # red
        font = 'courier'
        message = 'Invalid Expression'

        data_names = [name for name in self.origin.data]
        command = self.line_edit.text()
        real_command = self.subs_data_name(command, data_names) 
        print(real_command)
        try:
            exec(real_command)
            html = '<span style=" color:{color};font-family:{font}">{content}</span>'.format(
                    color=color_exp, font=font, content=command)
            self.text_pad.insertHtml(html)
            self.text_pad.insertPlainText('\n')
            self.command_index += 1
            self.origin.refresh_plot()
        except:
            html = '<span style=" color:{color};font-family:{font}">{content}</span>'.format(
                    color=color_err, font=font, content=message)
            self.text_pad.insertHtml(html)
            self.text_pad.insertPlainText('\n')
        self.line_edit.clear()

    @staticmethod
    def subs_data_name(command, data_names):
        result = []
        for token in re.split(r'\s+', command):
            #print(token)
            subscripting = re.match(r'(.+)\[-?\d+\]?', token)
            for name in data_names:
                if subscripting:
                    # this handles token like S0[1]
                    subscriptable_token = subscripting.group(1)
                    if subscriptable_token == name:
                        p = re.compile(subscriptable_token)
                        token = p.sub("self.origin.data['{}'][1]".format(subscriptable_token), token)
                else:
                    # this handles token like S0
                    if token == name:
                        p = re.compile(token)
                        token = p.sub("self.origin.data['{}'][1]".format(token), token)

            result.append(token)
        new_command = ' '.join(result)
        return new_command

if __name__ == "__main__":
    sb = DataEditor.subs_data_name
    names = ['S0', 'S1', 'S10']
    print(sb('S1 = S1 * 2 + S10 + S1[0]', names))
