import tkinter as tk
import tkinter.filedialog
import logging
import Main
from threading import Thread

class SyncnetGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SyncNet")

        # Open folder
        self.open_folder = tk.Button(root, text="Open Folder", command=self.openfolder)
        self.open_folder.grid(row= 0, column=0, pady=(20, 0))
        
        self.folder_path = ''
        self.folder_path_name = tk.StringVar()
        self.label_folder = tk.Label(root, textvariable=self.folder_path_name) 
        self.label_folder.grid(row= 1, column=0)

        # # Create checkbox
        # self.checkbox_names = ['All region', 'NCR', 'SLZ', 'NLZ', 'VIS', 'MIN']

        # self.checkbox_vars = [tk.BooleanVar() for _ in self.checkbox_names]
        # self.checkboxes = [tk.Checkbutton(root, text=region, variable=self.checkbox_vars[i],
        #                             command=lambda i=i: self.on_checkbox_selected(i))
        #             for i, region in enumerate(self.checkbox_names)]

        # for i, checkbox in enumerate(self.checkboxes):
        #     if i == 0:
        #         checkbox.grid(row=i+2, column=0, sticky='w',padx=20)  # Set sticky to 'w' for left alignment
        #     else:
        #         checkbox.grid(row=i+2, column=0, sticky='w', padx=50)  # Add padx for indentation

        # Create a Text widget to display logs
        self.log_text = tk.Text(root, wrap='word', height=20, width=100)
        self.log_text.grid(row=2, column=0, padx=10, pady=10)

        self.text_update = tk.StringVar()
        self.label = tk.Label(root, textvariable=self.text_update) 
        self.label.grid(row=3, sticky='w', padx=10, pady=0)

        # Create a Progressbar widget
        # self.progressbar = ttk.Progressbar(root, length=200, orient='horizontal')
        # self.progressbar.grid(row=len(self.checkbox_names) + 2, column=1, sticky='w', padx=10, pady=0)
        
        # Submit button
        self.run_button = tk.Button(root, text="Run Script", command=self.run_script)
        self.run_button.grid(row=4, column=0, pady=10)

        # Submit button
        self.finish_button = tk.Button(root, text="Quit", command=self.finish)
        self.finish_button.grid(row=5, column=0, pady=10)
        self.hide_button()

        # Configure logging with a custom handler
        self.setup_logging()    

    def hide_button(self):
        self.finish_button.grid_forget()

    def finish(self):
        root.quit()
            

    def openfolder(self):
            self.folder_path = tk.filedialog.askdirectory()
            self.folder_path_name.set(self.folder_path)
            
    def on_checkbox_selected(self, index):
            # If "All Region" is selected, uncheck other checkboxes
            if index == 0 and self.checkbox_vars[0].get():
                for i in range(1, len(self.checkbox_vars)):
                    self.checkbox_vars[i].set(True)
            # If any other checkbox is selected, uncheck "All Region"
            elif index != 0:
                self.checkbox_vars[0].set(False)

    def check_selected_checkboxes(self):
        selected_checkboxes = [self.checkbox_names[i] for i in range(len(self.checkbox_vars)) if self.checkbox_vars[i].get()]

        if selected_checkboxes:
            print("Selected checkboxes:", selected_checkboxes)
        else:
            print("No checkboxes selected.")

    def setup_logging(self):
        # Create a logger and set its level
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        # Create a custom handler for inserting logs into the Text widget
        log_handler = LogHandler(self.log_text)

        self.logger.addHandler(log_handler)
        self.logger.info("--- Please upload the folder path of your raw data")
        # self.logger.info("--- Select the region you would like to process")

    def run_script(self):
        # if self.folder_path:
        
        #     self.run_button.config(state=tk.DISABLED)
        #     thread = Thread(target = Main.run(root,self.text_update,self.folder_path))
        #     thread.start()
        #     # Main.run(root,self.text_update,self.folder_path)

        #     # show finish button
        #     self.finish_button.grid(row=5, column=0, pady=10)

        #     self.run_button.config(state=tk.NORMAL)
        # else:
        #     self.logger.info("Please upload a folder")
        if self.folder_path:
            self.run_button.config(state=tk.DISABLED)
            self.finish_button.grid_forget()

            # Use lambda to pass arguments to the thread function
            thread = Thread(target=lambda: self.run_thread(self.folder_path))
            thread.start()

            # Check the thread status periodically
            self.check_thread()
        else:
            self.logger.info("Please upload a folder")

    
    def check_thread(self):
        # if thread.is_alive():
        #     window.after(100,check_thread)
        # else:
        #     self.logger.info("Completedr")
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.root.after(100, self.check_thread)
        else:
            self.logger.info("Looping-----")

    

    def run_thread(self, folder_path):
        # Main.run(root, self.text_update, folder_path)
        try:
            Main.run(root, self.text_update, folder_path)
        except Exception as e:
            self.logger.error(f"Error in script: {str(e)}")
        finally:
            # Update GUI when the thread completes
            # self.root.after(0, self.thread_complete)
            self.thread_complete()

    def thread_complete(self):
        self.logger.info("------------Script completed.-----------")
        self.run_button.config(state=tk.NORMAL)
        self.finish_button.grid(row=5, column=0, pady=10)

        
    def generate_logs(self):
        self.logger.info("This is an information message.")
        self.logger.warning("This is a warning message.")
        self.logger.error("This is an error message.")


    def log_value(self, value):
        self.logger.info(value)

class LogHandler(logging.Handler):
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.yview(tk.END)  # Auto-scroll to the bottom

if __name__ == "__main__":
    root = tk.Tk()
    gui = SyncnetGUI(root)
    root.mainloop()
