import customtkinter as ctk
from tkinter import Listbox, filedialog, messagebox, StringVar, Text, Scrollbar, Canvas
from PIL import Image, ImageTk, ImageDraw
import json, os, base64, random, re, hashlib, io, smtplib, boto3, sys
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

class Utils:
    """Utility class containing helper methods for the application."""

    S3_BUCKET_NAME = '' #Removed for security puposes 
    SHARED_EMAIL = '' #Removed for security puposes 
    SHARED_PASSWORD = '' #Removed for security puposes 
    
    @staticmethod
    def s3_client():
        """Creates and returns an S3 client using configured AWS credentials."""
        return boto3.client(
            's3',
            aws_access_key_id='', #Removed for security puposes 
            aws_secret_access_key='' #Removed for security puposes 
        )

    @staticmethod
    def load_json_from_s3(key):
        """Loads JSON data from a specified S3 bucket key."""
        s3 = Utils.s3_client()
        try:
            response = s3.get_object(Bucket=Utils.S3_BUCKET_NAME, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            return data
        except s3.exceptions.NoSuchKey:
            return {}
        except (NoCredentialsError, PartialCredentialsError):
            raise Exception("Invalid AWS credentials.")
        except Exception as e:
            raise Exception(f"Error loading data from S3: {e}")

    @staticmethod
    def save_json_to_s3(data, key):
        """Saves JSON data to a specified S3 bucket key."""
        s3 = Utils.s3_client()
        try:
            s3.put_object(
                Bucket=Utils.S3_BUCKET_NAME,
                Key=key,
                Body=json.dumps(data, indent=4),
                ContentType='application/json'
            )
        except (NoCredentialsError, PartialCredentialsError):
            raise Exception("Invalid AWS credentials.")
        except Exception as e:
            raise Exception(f"Error saving data to S3: {e}")
        
    @staticmethod
    def load_json_from_local(file_path):
        """Loads JSON data from a local file."""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    return json.load(file)
            else:
                return {}
        except json.JSONDecodeError:
            raise Exception(f"Error decoding JSON from file: {file_path}")
        except Exception as e:
            raise Exception(f"Error loading data from local file: {e}")

    @staticmethod
    def save_json_to_local(data, file_path):
        """Saves JSON data to a local file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            raise Exception(f"Error saving data to local file: {e}")

    @staticmethod
    def resource_path(relative_path):
        """ Get the absolute path to a resource, works for PyInstaller's --onefile mode """
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    @staticmethod
    def encode_image_to_base64(image_path):
        """Encodes an image to base64 format."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    @staticmethod
    def round_image(image_path, size=(100, 100)):
        """Creates a rounded version of an image."""
        image = Image.open(image_path).resize(size).convert("RGBA")
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        rounded_image = Image.new("RGBA", size)
        rounded_image.paste(image, (0, 0), mask=mask)
        return rounded_image
    
    @staticmethod
    def round_image_from_data(image_data, size=(100, 100)):
        """Creates a rounded version of an image from image data."""
        image = Image.open(io.BytesIO(image_data)).resize(size).convert("RGBA")
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        rounded_image = Image.new("RGBA", size)
        rounded_image.paste(image, (0, 0), mask=mask)
        return rounded_image
    
    @staticmethod
    def validate_name(name):
        return bool(re.fullmatch(r"[A-Za-z ]+", name))

    @staticmethod
    def validate_address(address):
        return bool(re.fullmatch(r"[A-Za-z0-9 ,]+", address))

    @staticmethod
    def validate_phone_number(phone_number):
        """Ensures the phone number has exactly 10 digits, allowing spaces and dashes."""
        digits = re.sub(r"\D", "", phone_number) 
        return bool(re.fullmatch(r"[0-9 -]+", phone_number)) and len(digits) == 10
    
    @staticmethod
    def format_phone_number(phone_number):
        """Formats a phone number to XXX-XXX-XXXX."""
        digits = re.sub(r"\D", "", phone_number) 
        if len(digits) == 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        return phone_number

    @staticmethod
    def validate_date_of_birth(dob):
        return bool(re.fullmatch(r"\d{2}-\d{2}-\d{4}", dob))

    @staticmethod
    def validate_skills(skills):
        return bool(re.fullmatch(r"[A-Za-z, ]+", skills))

    @staticmethod
    def validate_email(email):
        """Validate the email format and check if it already exists in the system."""
        if not re.fullmatch(r"[A-Za-z0-9._%+-]+@gmail\.com", email):
            return False

        try:
            pending_employees = Utils.load_json_from_s3("pending_employees.json")
        except Exception:
            pending_employees = {}

        try:
            employees = Utils.load_json_from_s3("employees.json")
        except Exception:
            employees = {}

        for emp_data in pending_employees.values():
            if emp_data.get("Email") == email:
                return False

        for emp_data in employees.values():
            if emp_data.get("Email") == email:
                return False

        return True

    @staticmethod
    def validate_password(password):
        return len(password) >= 8
    
    @staticmethod
    def hash_password(password):
        """Hashes a password using SHA-256."""
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return hashed
    
    @staticmethod
    def create_ctk_image_from_base64(encoded_image, size=(100, 100)):
        """Decodes a base64-encoded image and returns a CTkImage object."""
        image_data = base64.b64decode(encoded_image)
        image = Image.open(io.BytesIO(image_data)).resize(size)
        return ctk.CTkImage(dark_image=image, size=size)

    @staticmethod
    def show_employee_info(employee, employee_id, parent_window=None):
        """Displays a pop-up window with detailed information about an employee."""
        info_window = ctk.CTkToplevel(parent_window)
        info_window.title(f"Employee {employee_id} Details")

        screen_width = info_window.winfo_screenwidth()
        screen_height = info_window.winfo_screenheight()
        window_width = 520
        window_height = 200
        x_cord = int((screen_width / 2) - (window_width / 2))
        y_cord = int((screen_height / 2) - (window_height / 2))
        info_window.geometry(f"{window_width}x{window_height}+{x_cord}+{y_cord}")
        
        info_window.attributes('-topmost', True)
        info_window.after(500, lambda: info_window.attributes('-topmost', False))

        main_frame = ctk.CTkFrame(info_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        if employee.get("image"):
            decoded_image = Utils.create_ctk_image_from_base64(employee["image"], size=(140, 140))
            image_label = ctk.CTkLabel(main_frame, image=decoded_image, text="")
            image_label.image = decoded_image
            image_label.grid(row=0, column=0, rowspan=2, padx=(0, 20), sticky="nswe")

        details_text = "\n".join(
            f"{key}: {value}" for key, value in employee.items() if key != "image" and key != "Password"
        )

        details_label = ctk.CTkLabel(
            main_frame,
            text=details_text,
            justify="left",
            padx=10,
            font=("Arial", 16)
        )
        details_label.grid(row=0, column=1, sticky="w")

    @staticmethod
    def show_images(job_id, json_file="completed_jobs.json", use_s3 = True):
        """Displays images associated with a given job ID from a JSON file."""
        
        try:
            if use_s3:
                jobs = Utils.load_json_from_s3(json_file)
            else:
                with open(json_file, "r") as file:
                    jobs = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError, Exception):
            return
        
        if job_id not in jobs or "Images" not in jobs[job_id] or not jobs[job_id]["Images"]:
            messagebox.showwarning("No Images", f"No images found for Job ID: {job_id}")
            return
        
        images_window = ctk.CTkToplevel()
        images_window.title(f"Images for Job ID: {job_id}")
        
        screen_width = images_window.winfo_screenwidth()
        screen_height = images_window.winfo_screenheight()
        window_width = 450
        window_height = 500
        x_cord = int((screen_width / 2) - (window_width / 2))
        y_cord = int((screen_height / 2) - (window_height / 2))
        images_window.geometry(f"{window_width}x{window_height}+{x_cord}+{y_cord}")

        images_window.attributes('-topmost', True)
        images_window.after(500, lambda: images_window.attributes('-topmost', False))
        
        frame = ctk.CTkFrame(images_window, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        canvas = Canvas(frame)
        canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar = Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        images_frame = ctk.CTkFrame(canvas, fg_color="transparent")
        canvas.create_window((0, 0), window=images_frame, anchor="nw")
        
        images = jobs[job_id]["Images"]

        for idx, encoded_image in enumerate(images):          
            decoded_image = Utils.create_ctk_image_from_base64(encoded_image, size=(400, 400))       
            image_label = ctk.CTkLabel(images_frame, image=decoded_image, text="")
            image_label.image = decoded_image  
            image_label.grid(row=idx, column=0, pady=10, padx=10)
        
        images_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

class EmployeeDashboard(ctk.CTkFrame):
    """A GUI dashboard for employee management using CustomTkinter."""
    def __init__(self, parent, controller, employee_data):
        """Initialize the dashboard layout and components."""
        super().__init__(parent)
        self.controller = controller
        self.employee_data = employee_data
        self.init_dashboard()
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        sidebar_frame = ctk.CTkFrame(self, width=150, corner_radius=0)
        sidebar_frame.grid(row=0, column=0, sticky="ns")
        
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        tab_names = ["Home", "Edit Information", "View Jobs", "Notifications", "Log Out"]
        tab_frames = []

        for tab_name in tab_names:
            tab_frame = ctk.CTkFrame(content_frame)
            tab_frame.grid(row=0, column=0, sticky="nsew")
            tab_frame.grid_columnconfigure(0, weight=1)
            tab_frame.grid_rowconfigure(0, weight=1)
            tab_frames.append(tab_frame)

        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        self.init_home_tab(tab_frames[0])
        self.init_edit_info_tab(tab_frames[1])
        self.init_view_jobs_tab(tab_frames[2])
        self.init_notifications_tab(tab_frames[3])
        
        tab_labels = []
        indicator_bars = []
        
        for i, tab_name in enumerate(tab_names):
            tab_label = ctk.CTkLabel(sidebar_frame, text=tab_name, font=("Arial", 12), anchor="w")
            tab_label.grid(row=i * 2, column=0, padx=10, pady=5, sticky="w")
            tab_labels.append(tab_label)

            
            indicator_bar = ctk.CTkFrame(sidebar_frame, height=2)
            indicator_bar.grid(row=i * 2 + 1, column=0, padx=10, sticky="ew")
            indicator_bars.append(indicator_bar)

            if tab_name == "Log Out":
                
                tab_label.bind("<Button-1>", lambda event: self.logout())
            else:
                
                tab_label.bind("<Button-1>", lambda event, frame=tab_frames[i], active_label=tab_label:
                               self.show_tab(frame, active_label, tab_labels, indicator_bars))
        
        self.show_tab(tab_frames[0], tab_labels[0], tab_labels, indicator_bars)

    def init_dashboard(self):
        """Initial setup for the EmployeeDashboard."""
        pass

    def refresh(self):
        """Refresh the content of the EmployeeDashboard."""
        for widget in self.winfo_children():
            widget.destroy()  
        self.init_dashboard()

    def show_tab(self, frame, active_label, tab_labels, indicator_bars):
        """Displays the specified frame and highlights the active tab."""
        frame.tkraise()  
        
        for label, bar in zip(tab_labels, indicator_bars):
            if label == active_label:
                label.configure(text_color="white")
                bar.configure(fg_color="blue")  
            else:
                label.configure(text_color="gray")
                bar.configure(fg_color="gray")

    def init_home_tab(self, frame):
        """Initialize the Home tab content with logged-in employee's information in the inner frame."""
        
        inner_frame = ctk.CTkFrame(frame, width=480, height=450)
        inner_frame.grid(row=0, column=0, sticky="", padx=10, pady=10)
        inner_frame.grid_propagate(False)
        inner_frame.grid_columnconfigure(0, weight=1)
        inner_frame.grid_rowconfigure(0, weight=0)
        inner_frame.grid_rowconfigure(1, weight=1)
        inner_frame.grid_rowconfigure(2, weight=1)
        
        full_name = self.employee_data.get("Name", "Employee")
        first_name = full_name.split()[0] if full_name else "Employee"

        if self.employee_data.get("image"):
            image_data = base64.b64decode(self.employee_data["image"])
            rounded_image = Utils.round_image_from_data(image_data, size=(150, 150))
            rounded_ctk_image = ctk.CTkImage(dark_image=rounded_image, size=(150, 150))

            image_label = ctk.CTkLabel(inner_frame, image=rounded_ctk_image, text="")
            image_label.image = rounded_ctk_image  
            image_label.grid(row=0, column=0, pady=(10, 2), sticky="n")

        greeting_label = ctk.CTkLabel(inner_frame, text=f"Welcome to Employee Dashboard {first_name}!", font=("Arial", 20))
        greeting_label.grid(row=1, column=0, padx=10, pady=(2, 5), sticky="n")

        
        info_text = "\n".join(
            f"{key}: {value}" for key, value in self.employee_data.items() if key != "Password" and key != "image"
        )

        info_label = ctk.CTkLabel(inner_frame, text=info_text, justify="center", font=("Arial", 18))
        info_label.grid(row=2, column=0, padx=10, pady=5, sticky="n")

    def init_edit_info_tab(self, frame):
        """Initialize the Edit Information tab for editing employee details."""
        
        inner_frame = ctk.CTkFrame(frame)
        inner_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        inner_frame.grid_propagate(False)
        inner_frame.grid_columnconfigure(0, weight=1)
        inner_frame.grid_columnconfigure(1, weight=1)

        def validate_input(validator, entry):
            """Validate input and change entry field color."""
            if not validator(entry.get()):
                entry.configure(border_color="red") 
            else:
                entry.configure(border_color="green") 

        def select_image():
            """Allow the user to select and upload an image for the employee."""
            file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
            if file_path:
                img = Utils.round_image(file_path, size=(100, 100))
                self.photo = ctk.CTkImage(img, size=(100, 100))
                self.image_label.configure(image=self.photo, text="")
                self.employee_data["image"] = Utils.encode_image_to_base64(file_path)

        def save_changes():
            """Validate user inputs, update employee information, and save it to the database."""
            if not Utils.validate_name(self.name_entry.get()):
                messagebox.showerror("Error", "Invalid Name. Only letters and spaces allowed.")
                return
            if not Utils.validate_address(self.address_entry.get()):
                messagebox.showerror("Error", "Invalid Address. Only letters, numbers, spaces, and commas allowed.")
                return
            if not Utils.validate_phone_number(self.phone_entry.get()):
                messagebox.showerror("Error", "Invalid Phone Number. Only 10 digits, spaces, and dashes allowed.")
                return
            if not Utils.validate_date_of_birth(self.dob_entry.get()):
                messagebox.showerror("Error", "Invalid Date of Birth. Use format MM-DD-YYYY.")
                return
            if not Utils.validate_skills(self.skills_entry.get()):
                messagebox.showerror("Error", "Invalid Skills. Only letters, spaces, and commas allowed.")
                return
            
            self.employee_data["Name"] = self.name_entry.get()
            self.employee_data["Address"] = self.address_entry.get()
            self.employee_data["Phone Number"] = Utils.format_phone_number(self.phone_entry.get())
            self.employee_data["Date of Birth"] = self.dob_entry.get()
            self.employee_data["Position"] = self.position_menu.get()
            self.employee_data["Skills"] = self.skills_entry.get()

            all_data = Utils.load_json_from_s3("employees.json")
            employee_id = self.employee_data["Employee ID"]
            all_data[employee_id] = self.employee_data
            Utils.save_json_to_s3(all_data, "employees.json")

            messagebox.showinfo("Success", "Information updated successfully!")

            if "EmployerDashboard" in self.controller.frames:
                    self.controller.frames["EmployerDashboard"].refresh()

            self.controller.show_frame("EmployeeDashboard", employee_data=self.employee_data) 
        
        if self.employee_data.get("image"):
            image_data = base64.b64decode(self.employee_data["image"])
            rounded_image = Utils.round_image_from_data(image_data, size=(150, 150))
            self.photo = ctk.CTkImage(rounded_image, size=(150, 150))
        else:
            placeholder_img = Utils.round_image(Utils.resource_path("777.png"), size=(150, 150))
            self.photo = ctk.CTkImage(placeholder_img, size=(150, 150))

        self.image_label = ctk.CTkLabel(inner_frame, image=self.photo, text="", width=100, height=100)
        self.image_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        self.image_button = ctk.CTkButton(inner_frame, text="Select Image", command=select_image)
        self.image_button.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.fields = [
            ("Name", "Enter Full Name", Utils.validate_name, self.employee_data.get("Name")),
            ("Address", "Enter Address", Utils.validate_address, self.employee_data.get("Address")),
            ("Phone Number", "Enter Phone Number", Utils.validate_phone_number, self.employee_data.get("Phone Number")),
            ("Date of Birth", "MM-DD-YYYY", Utils.validate_date_of_birth, self.employee_data.get("Date of Birth")),
            ("Skills", "Enter Skills (comma-separated)", Utils.validate_skills, self.employee_data.get("Skills")),
            ("Position", "Select Position", None, self.employee_data.get("Position"))
        ]

        self.entries = []
        for i, (label_text, placeholder, validator, value) in enumerate(self.fields, start=2):
            label = ctk.CTkLabel(inner_frame, text=label_text + ":", anchor="e", width=100)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="e")

            if label_text == "Position":
                self.position_menu = ctk.CTkOptionMenu(
                    inner_frame, values=["Assistant", "Foreman", "Mason", "Irrigation technician", "Gardener", "Machine operator", "Arborist", "Groundskeeper"], width=300
                )
                self.position_menu.set(value)
                self.position_menu.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            else:
                entry = ctk.CTkEntry(inner_frame, placeholder_text=placeholder, width=300)
                entry.insert(0, value)  
                entry.grid(row=i, column=1, padx=10, pady=5, sticky="w")
                if validator:
                    entry.bind("<FocusOut>", lambda e, v=validator, ent=entry: validate_input(v, ent))
                self.entries.append(entry)

        self.name_entry, self.address_entry, self.phone_entry, self.dob_entry, self.skills_entry = self.entries

        save_button = ctk.CTkButton(inner_frame, text="Save Changes", command=save_changes, width=150)
        save_button.grid(row=len(self.fields) + 2, column=0, columnspan=2, pady=20)

    def init_view_jobs_tab(self, frame):
        """Initialize the View Jobs tab content for employees."""

        selected_images = []
        
        image_count_label = ctk.CTkLabel(frame, text="No images selected", anchor="w")
        image_count_label.grid(row=3, column=0, padx=10, pady=(5, 10))
        
        def load_jobs():
            """Load and display jobs available for the employee's position."""
            job_listbox.delete(0, 'end')
            try:
                jobs = Utils.load_json_from_s3("jobs.json")
                employee_position = self.employee_data.get('Position')  
                for job_id, job_info in jobs.items():
                    if job_info['Position'] == employee_position:  
                        job_listbox.insert("end", f"{job_info['Job ID']} | {job_info['Date']} | {job_info['Position']}")
            except Exception:
                
                messagebox.showinfo("No Jobs Found", "No available job postings found.")
        
        def show_job_details(event):
            """Display detailed information about the selected job."""
            selected_index = job_listbox.curselection()
            if selected_index:
                job_id = job_listbox.get(selected_index).split(" | ")[0]
                try:
                    jobs = Utils.load_json_from_s3("jobs.json")
                    job_info = jobs.get(job_id)
                    if job_info:
                        job_details_text.config(state="normal")
                        job_details_text.delete("1.0", "end")
                        job_details_text.insert("end", f"Job ID: {job_info['Job ID']}\n")
                        job_details_text.insert("end", f"Date: {job_info['Date']}\n")
                        job_details_text.insert("end", f"Position: {job_info['Position']}\n")
                        job_details_text.insert("end", f"Description:\n{job_info['Job Description']}\n")
                        job_details_text.config(state="disabled")
                except Exception:
                    
                    messagebox.showinfo("No Jobs Found", "No job postings available.")
        
        def select_images():
            """Allow the user to select images to associate with a job."""
            nonlocal selected_images
            files = filedialog.askopenfilenames(filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif")])
            if files:
                selected_images.extend(files)
                image_count_label.configure(text=f"{len(selected_images)} images selected.")
        
        def upload_images():
            """Upload selected images to the corresponding job record."""
            nonlocal selected_images
            selected_index = job_listbox.curselection()
            if selected_index:
                job_id = job_listbox.get(selected_index).split(" | ")[0]
                
                if not selected_images:
                    messagebox.showwarning("Warning", "Please select image files to upload.")
                    return
                
                encoded_images = []
                for image_path in selected_images:
                    try:
                        encoded_images.append(Utils.encode_image_to_base64(image_path))
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to encode image {image_path}: {e}")
                        return
                
                try:
                    jobs = Utils.load_json_from_s3("jobs.json")
                except Exception:
                    jobs = {}
                
                if job_id not in jobs:
                    messagebox.showerror("Error", f"Job ID {job_id} not found.")
                    return

                if "Images" not in jobs[job_id]:
                    jobs[job_id]["Images"] = []
                
                jobs[job_id]["Images"].extend(encoded_images)
                
                Utils.save_json_to_s3(jobs, "jobs.json")

                messagebox.showinfo("Success", f"{len(encoded_images)} images uploaded to Job ID: {job_id}")
                selected_images = []  
                image_count_label.configure(text="No images selected")  

            else:
                messagebox.showwarning("No Selection", "Please select a job from the list.")

        def show_selected_job_images():
            """Show all images associated with the selected job."""
            selected_index = job_listbox.curselection()
            if selected_index:
                job_id = job_listbox.get(selected_index).split(" | ")[0]
                Utils.show_images(job_id, json_file="jobs.json", use_s3=True)
            else:
                messagebox.showwarning("No Selection", "Please select a job from the list.")
        
        def complete_job():
            """Mark the selected job as completed and move it to the completed jobs database."""
            selected_index = job_listbox.curselection()
            if selected_index:
                job_id = job_listbox.get(selected_index).split(" | ")[0]

                try:
                    jobs = Utils.load_json_from_s3("jobs.json")
                except Exception:
                    messagebox.showerror("Error", "Jobs data file not found or is invalid.")
                    return
                
                if job_id not in jobs:
                    messagebox.showerror("Error", f"Job ID {job_id} not found in jobs.")
                    return

                try:
                    completed_jobs = Utils.load_json_from_s3("completed_jobs.json")
                except Exception:
                    
                    print("Error loading completed jobs data from S3.")
                    completed_jobs = {}
                
                completed_jobs[job_id] = jobs.pop(job_id)

                try:
                    Utils.save_json_to_s3(jobs, "jobs.json")
                except Exception:
                    messagebox.showerror("Error", "Failed to save jobs data.")

                try:
                    Utils.save_json_to_s3(completed_jobs, "completed_jobs.json")
                except Exception:
                    print("Error saving completed jobs data to S3.")

                messagebox.showinfo("Success", f"Job ID {job_id} has been completed.")

                job_details_text.config(state="normal")
                job_details_text.delete("1.0", "end")
                job_details_text.config(state="disabled")

                if "EmployerDashboard" in self.controller.frames:
                    self.controller.frames["EmployerDashboard"].refresh()

                load_jobs()  
            else:
                messagebox.showwarning("No Selection", "Please select a job from the list.")
        
        job_listbox = Listbox(frame, height=8, font=("Arial", 16))
        job_listbox.grid(row=0, column=0, columnspan=4, padx=10, pady=(10, 10), sticky="nsew")
        
        job_details_text = Text(frame, wrap="word", font=("Arial", 16), height=10, state="disabled")
        job_details_text.grid(row=4, column=0, columnspan=4, padx=10, pady=(10, 10), sticky="nsew")
   
        select_images_button = ctk.CTkButton(frame, text="Select Images", width=120, command=select_images)
        select_images_button.grid(row=1, column=0, padx=5, pady=(10, 10))

        upload_images_button = ctk.CTkButton(frame, text="Upload Images", width=120, command=upload_images)
        upload_images_button.grid(row=1, column=1, padx=5, pady=(10, 10))

        show_images_button = ctk.CTkButton(frame, text="Show Images", width=120, command=show_selected_job_images)
        show_images_button.grid(row=1, column=2, padx=5, pady=(10, 10))

        complete_job_button = ctk.CTkButton(frame, text="Complete Job", width=120, command=complete_job)
        complete_job_button.grid(row=1, column=3, padx=5, pady=(10, 10))
        
        job_listbox.bind("<<ListboxSelect>>", show_job_details)
        
        load_jobs()
        
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(2, weight=1)
        frame.grid_columnconfigure(3, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(4, weight=1)

    def init_notifications_tab(self, frame):
        """Initialize the Notifications tab content with filtering options."""
        notifications = []

        def load_messages():
            """Load messages for the logged-in employee."""
            nonlocal notifications
            employee_id = self.employee_data.get("Employee ID")
            position = self.employee_data.get("Position")
            employee_name = self.employee_data.get("Name")

            try:
                all_messages = Utils.load_json_from_s3("messages.json")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load messages: {e}")
                all_messages = {}

            notifications.clear()

            if "All Employees" in all_messages:
                notifications.extend(
                    [{"To": "All Employees", "Message": msg["Message"], "Date": msg["Date"]}
                    for msg in all_messages["All Employees"]]
                )

            if position in all_messages:
                notifications.extend(
                    [{"To": f"{position}s", "Message": msg["Message"], "Date": msg["Date"]}
                    for msg in all_messages[position]]
                )

            if employee_id in all_messages:
                notifications.extend(
                    [{"To": f"{employee_name}", "Message": msg["Message"], "Date": msg["Date"]}
                    for msg in all_messages[employee_id]]
                )

            update_notifications_display("All")

        def update_notifications_display(filter_option):
            """Display the loaded messages based on the filter option."""
            notifications_text.config(state="normal")
            notifications_text.delete("1.0", "end")

            filtered_notifications = []

            if filter_option == "All":
                filtered_notifications = notifications
            elif filter_option == "Position":
                filtered_notifications = [note for note in notifications if note["To"] != "All Employees" and "s" in note["To"]]
            elif filter_option == "Personal":
                filtered_notifications = [note for note in notifications if "All Employees" not in note["To"] and "s" not in note["To"]]

            if not filtered_notifications:
                notifications_text.insert("end", "No notifications available.")
            else:
                for i, note in enumerate(filtered_notifications):
                    notifications_text.insert(
                        "end",
                        f"To: {note['To']}\nDate: {note['Date']}\nMessage:\n{note['Message']}\n\n"
                    )

                    if i < len(filtered_notifications) - 1:
                        notifications_text.insert("end", "-" * 70 + "\n\n")

            notifications_text.config(state="disabled")

        def filter_notifications():
            """Filter notifications based on the selected dropdown option."""
            selected_filter = filter_var.get()
            update_notifications_display(selected_filter)

        notifications_label = ctk.CTkLabel(frame, text="Notifications:", font=("Arial", 14), anchor="w")
        notifications_label.grid(row=0, column=0, padx=10, pady=(5, 5), sticky="nw")

        notifications_text = Text(frame, wrap="word", font=("Arial", 16), state="disabled", height=20, borderwidth=0)
        notifications_text.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        filter_frame = ctk.CTkFrame(frame, fg_color="transparent")
        filter_frame.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")
        filter_frame.grid_columnconfigure(0, weight=1)
        filter_frame.grid_columnconfigure(1, weight=0)

        filter_var = ctk.StringVar(value="All")
        filter_dropdown = ctk.CTkOptionMenu(
            filter_frame,
            variable=filter_var,
            values=["All", "Position", "Personal"],
            width=150
        )
        filter_dropdown.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        filter_button = ctk.CTkButton(filter_frame, text="Filter", command=filter_notifications, width=100)
        filter_button.grid(row=0, column=1, padx=5, pady=5)

        load_messages()

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=0)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_rowconfigure(2, weight=0)


    def logout(self):
        """Logs out the user and returns to the login screen."""
        self.controller.logout()
    
class EmployerDashboard(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_dashboard()  
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
        sidebar_frame = ctk.CTkFrame(self, width=150, corner_radius=0)
        sidebar_frame.grid(row=0, column=0, sticky="ns")
        
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        tab_names = [
            "Home", "Pending Employees", "Manage Employees",
            "Inform Employees", "Message Archive", "Post Jobs", "Completed Jobs", "Log Out"
        ]
        tab_frames = []

        for tab_name in tab_names:
            tab_frame = ctk.CTkFrame(content_frame)
            tab_frame.grid(row=0, column=0, sticky="nsew")
            tab_frame.grid_columnconfigure(0, weight=1)
            tab_frame.grid_rowconfigure(0, weight=1)
            tab_frames.append(tab_frame)
        
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        self.view_employees_frame = tab_frames[2]
        self.view_notifications_frame = tab_frames[4]
        
        self.init_home_tab(tab_frames[0])
        self.init_pending_employees_tab(tab_frames[1])
        self.init_view_employees_tab(tab_frames[2])
        self.init_inform_employee_tab(tab_frames[3])
        self.init_notifications_tab(tab_frames[4])
        self.init_post_jobs_tab(tab_frames[5])
        self.init_completed_jobs_tab(tab_frames[6])
        
        tab_labels = []
        indicator_bars = []
        
        for i, tab_name in enumerate(tab_names):
            tab_label = ctk.CTkLabel(sidebar_frame, text=tab_name, font=("Arial", 12), anchor="w")
            tab_label.grid(row=i * 2, column=0, padx=10, pady=5, sticky="w")
            tab_labels.append(tab_label)

            indicator_bar = ctk.CTkFrame(sidebar_frame, height=2)
            indicator_bar.grid(row=i * 2 + 1, column=0, padx=10, sticky="ew")
            indicator_bars.append(indicator_bar)

            if tab_name == "Log Out":
                
                tab_label.bind("<Button-1>", lambda event: self.logout())
            else:
                
                tab_label.bind("<Button-1>", lambda event, frame=tab_frames[i], active_label=tab_label:
                               self.show_tab(frame, active_label, tab_labels, indicator_bars))
        
        self.show_tab(tab_frames[0], tab_labels[0], tab_labels, indicator_bars)

    def init_dashboard(self):
        """Initial setup for the EmployerDashboard."""
        pass

    def refresh(self):
        """Refresh the content of the EmployerDashboard."""
        for widget in self.winfo_children():
            widget.destroy()  
        self.init_dashboard()

    def show_tab(self, frame, active_label, tab_labels, indicator_bars):
        """Displays the specified frame and highlights the active tab."""
        frame.tkraise()  
        
        for label, bar in zip(tab_labels, indicator_bars):
            if label == active_label:
                label.configure(text_color="white")
                bar.configure(fg_color="blue")  
            else:
                label.configure(text_color="gray")
                bar.configure(fg_color="gray")

    def init_home_tab(self, frame):
        """Initialize the Home tab content with an image and welcome text."""
        main_frame = ctk.CTkFrame(frame)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_rowconfigure(0, weight=1)  
        main_frame.grid_rowconfigure(1, weight=0)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        logo_path = Utils.resource_path("222.png") 
        try:
            logo_image = Image.open(logo_path)
            img_width, img_height = logo_image.size
            max_width, max_height = 500, 200  
            scale_factor = min(max_width / img_width, max_height / img_height)

            new_width = int(img_width * scale_factor)
            new_height = int(img_height * scale_factor)
            resized_logo_image = logo_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            ctk_logo_image = ctk.CTkImage(light_image=resized_logo_image, size=(new_width, new_height))
            
            image_label = ctk.CTkLabel(main_frame, image=ctk_logo_image, text="")
            image_label.grid(row=0, column=0, pady=(10, 0), sticky="nsew")

        except Exception as e:
            print(f"Error loading image: {e}")

        text_frame = ctk.CTkFrame(main_frame, width=480, height=150)
        text_frame.grid(row=1, column=0, padx=10, pady=(0, 0), sticky="")
        text_frame.grid_propagate(False)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)

        welcome_message = "Welcome to the Crosscut Landscaping's \n Employer Dashboard \n Michael Kraut!"
        welcome_label = ctk.CTkLabel(
            text_frame,
            text=welcome_message,
            font=("Arial", 20, "bold"),
            anchor="center"
        )
        welcome_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    def init_pending_employees_tab(self, frame):
        """Initialize the Pending Employees tab content."""
        
        def load_pending_employees():
            """Load pending employees from the S3 bucket and display them in the listbox."""
            self.employee_listbox.delete(0, "end")
            try:
                self.pending_employees = Utils.load_json_from_s3("pending_employees.json")

                for emp_id, emp_info in self.pending_employees.items():
                    self.employee_listbox.insert("end", f"{emp_id} | {emp_info.get('Position', 'N/A')} | {emp_info.get('Name', 'Unknown')}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load pending employee data: {e}")

        def show_employee_info():
            """Show the selected employee's information in a new pop-up window."""
            selected_index = self.employee_listbox.curselection()
            if selected_index:
                selected_id = list(self.pending_employees.keys())[selected_index[0]]
                employee = self.pending_employees[selected_id]
                Utils.show_employee_info(employee, selected_id, self)
            else:
                messagebox.showwarning("No Selection", "Please select an employee from the list.")

        def send_acceptance_email(recipient_email):
            """Send an email notification to the accepted employee."""
            subject = "Your Account Has Been Accepted"
            body = "Your account with Crosscut Landscaping has been accepted. You can now log in to your dashboard using your email and password."
            message = f"Subject: {subject}\n\n{body}"

            try:
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(Utils.SHARED_EMAIL, Utils.SHARED_PASSWORD)
                    server.sendmail(Utils.SHARED_EMAIL, recipient_email, message)
            except Exception:
                messagebox.showinfo("Invalid Email", f"Failed to send acceptance email to {recipient_email} .")

        def accept_employee():
            """Accept the selected employee and move them to employees.json."""
            selected_index = self.employee_listbox.curselection()
            if selected_index:
                selected_id = list(self.pending_employees.keys())[selected_index[0]]
                employee = self.pending_employees[selected_id]

                try:
                    employees = Utils.load_json_from_s3("employees.json")
                except Exception:
                    employees = {}

                employees[selected_id] = employee

                try:
                    Utils.save_json_to_s3(employees, "employees.json")
                except Exception:
                    pass 

                del self.pending_employees[selected_id]

                try:
                    Utils.save_json_to_s3(self.pending_employees, "pending_employees.json")
                    messagebox.showinfo("Employee Accepted", f"Employee {selected_id} has been accepted.")

                    if "Email" in employee:
                        send_acceptance_email(employee["Email"])

                except Exception:
                    pass

                self.load_pending_employees() 
                self.init_view_employees_tab(self.view_employees_frame)

            else:
                messagebox.showwarning("No Selection", "Please select an employee from the list.")

        def reject_employee():
            """Reject the selected employee and remove them from pending_employees.json."""
            selected_index = self.employee_listbox.curselection()
            if selected_index:
                selected_id = list(self.pending_employees.keys())[selected_index[0]]

                confirm = messagebox.askyesno("Reject Employee", f"Are you sure you want to reject employee {selected_id}?")
                if confirm:
                    del self.pending_employees[selected_id]

                    try:
                        Utils.save_json_to_s3(self.pending_employees, "pending_employees.json")
                    except Exception:
                        pass  

                    messagebox.showinfo("Employee Rejected", f"Employee {selected_id} has been rejected.")
                    self.load_pending_employees() 

            else:
                messagebox.showwarning("No Selection", "Please select an employee from the list.")

        self.load_pending_employees = load_pending_employees
        self.show_employee_info = show_employee_info
        self.accept_employee = accept_employee
        self.reject_employee = reject_employee
        
        self.employee_listbox = Listbox(frame, height=10, width=50, font=("Arial", 18))
        self.employee_listbox.grid(row=0, column=0, columnspan=3, pady=10, sticky="nsew")
       
        self.load_pending_employees()
       
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.grid(row=1, column=0, columnspan=1, pady=(20, 10), sticky="ew")
               
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

        show_info_button = ctk.CTkButton(button_frame, text="Show Employee Info", command=self.show_employee_info)
        show_info_button.grid(row=0, column=0, padx=5)

        accept_button = ctk.CTkButton(button_frame, text="Accept Employee", command=self.accept_employee)
        accept_button.grid(row=0, column=1, padx=5)

        reject_button = ctk.CTkButton(button_frame, text="Reject Employee", command=self.reject_employee)
        reject_button.grid(row=0, column=2, padx=5)

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

    def init_view_employees_tab(self, frame):
        """Initialize the View Employees tab content."""
        try:
            self.employees = Utils.load_json_from_s3("employees.json")
        except Exception:
            self.employees = {}
        
        top_frame = ctk.CTkFrame(frame, fg_color="transparent")
        top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=1)
        top_frame.grid_columnconfigure(2, weight=1)
        
        position_var = ctk.StringVar(value="All Positions")
        position_menu = ctk.CTkOptionMenu(
            top_frame,
            variable=position_var,
            values=["All Positions"] + list(set(emp.get("Position", "Unknown") for emp in self.employees.values())),
            width=150
        )
        position_menu.grid(row=0, column=0, padx=5, pady=5)
        
        search_key_var = ctk.StringVar(value="Select Key")
        search_keys = ["Name", "Email", "Phone Number", "Address", "Date of Birth", "Skills"]
        search_key_menu = ctk.CTkOptionMenu(
            top_frame,
            variable=search_key_var,
            values=search_keys,
            width=150
        )
        search_key_menu.grid(row=0, column=1, padx=5, pady=5)
        
        search_entry = ctk.CTkEntry(top_frame, placeholder_text="Search by selected key...", width=170)
        search_entry.grid(row=0, column=2, padx=5, pady=5)
        
        employee_listbox = Listbox(frame, height=24, width=50, font=("Arial", 18))
        employee_listbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        self.update_employee_listbox(employee_listbox, self.employees.values())
        self.filtered_employees = list(self.employees.values())
       
        def search_employees():
            """Search employees based on user input criteria."""
            search_text = search_entry.get().lower()
            selected_position = position_var.get()
            selected_key = search_key_var.get()

            self.filtered_employees = [
                emp for emp in self.employees.values()
                if (selected_position == "All Positions" or emp.get("Position") == selected_position) and
                (selected_key == "Select Key" or search_text in str(emp.get(selected_key, "")).lower())
            ]
            self.update_employee_listbox(employee_listbox, self.filtered_employees)
        
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        button_frame.grid_columnconfigure(3, weight=1)
        
        search_button = ctk.CTkButton(button_frame, text="Search", command=search_employees, width=120)
        search_button.grid(row=0, column=0, padx=5, pady=5)
        
        def clear_search():
            """Clear the search input and reset the employee list."""
            search_entry.delete(0, 'end')
            position_var.set("All Positions")
            self.filtered_employees = list(self.employees.values())
            self.update_employee_listbox(employee_listbox, self.filtered_employees)

        clear_button = ctk.CTkButton(button_frame, text="Clear Search", command=clear_search, width=120)
        clear_button.grid(row=0, column=1, padx=5, pady=5)
        
        def show_selected_employee():
            """Display detailed information about the selected employee."""
            selected_index = employee_listbox.curselection()
            if selected_index:
                selected_employee = self.filtered_employees[selected_index[0]]
                selected_id = selected_employee["Employee ID"]
                Utils.show_employee_info(selected_employee, selected_id, self)
            else:
                messagebox.showwarning("No Selection", "Please select an employee from the list.")

        show_info_button = ctk.CTkButton(button_frame, text="Show Employee Info", command=show_selected_employee, width=120)
        show_info_button.grid(row=0, column=2, padx=5, pady=5)

        def fire_employee():
            """Remove the selected employee from the database."""
            selected_index = employee_listbox.curselection()
            if selected_index:
                selected_id = list(self.employees.keys())[selected_index[0]]
                confirm = messagebox.askyesno("Fire Employee", f"Are you sure you want to fire employee {selected_id}?")
                if confirm:
                    del self.employees[selected_id]
                    try:
                        Utils.save_json_to_s3(self.employees, "employees.json")
                        messagebox.showinfo("Employee Fired", f"Employee {selected_id} has been fired.")
                        self.update_employee_listbox(employee_listbox, self.employees.values())  
                    except Exception:
                        messagebox.showerror("Error", "Failed to update employee data.")
            else:
                messagebox.showwarning("No Selection", "Please select an employee from the list.")

        fire_button = ctk.CTkButton(button_frame, text="Fire Employee", command=fire_employee, width=120)
        fire_button.grid(row=0, column=3, padx=5, pady=5)
        
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

    def update_employee_listbox(self, listbox, employees):
        """Updates the Listbox with provided employee data."""
        listbox.delete(0, "end")
        for emp in employees:
            listbox.insert("end", f"{emp['Employee ID']} | {emp.get('Position', 'N/A')} | {emp['Name']}")

    def init_post_jobs_tab(self, frame):
        """Initialize the Post Jobs tab content."""      
        
        def generate_job_id():
            return str(random.randint(10000, 99999))
        
        def save_job():
            position = position_var.get()
            date = date_entry.get()
            description = description_text.get("1.0", "end").strip()

            if position == "Select Position":
                messagebox.showwarning("Warning", "Please select a position.")
                return
            if not date:
                messagebox.showwarning("Warning", "Please enter a date.")
                return
            if not description:
                messagebox.showwarning("Warning", "Please enter a job description.")
                return

            job_id = generate_job_id()

            try:
                jobs = Utils.load_json_from_s3("jobs.json")
            except Exception:
                print("Error loading jobs data from S3.")
                jobs = {}

            jobs[job_id] = {
                "Job ID": job_id,
                "Date": date,
                "Job Description": description,
                "Position": position
            }

            try:
                Utils.save_json_to_s3(jobs, "jobs.json")
                messagebox.showinfo("Success", "Job posted successfully!")
            except Exception:
                print("Error saving jobs data to S3.")

            if "EmployeeDashboard" in self.controller.frames:
                self.controller.frames["EmployeeDashboard"].refresh()

            position_var.set("Select Position")
            date_entry.delete(0, 'end')
            description_text.delete("1.0", "end")
            load_jobs()
        
        job_desc_label = ctk.CTkLabel(frame, text="Job Description:", anchor="w")
        job_desc_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        description_text = Text(frame, wrap="word", height=10, font=("Arial", 16), borderwidth=0, relief="flat")
        description_text.grid(row=1, column=0, padx=8, pady=(5, 10), sticky="nsew")
        
        input_frame = ctk.CTkFrame(frame, fg_color="transparent")
        input_frame.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")
        
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_columnconfigure(2, weight=1)
        
        position_var = ctk.StringVar(value="Select Position")
        positions = ["Assistant", "Foreman", "Mason", "Irrigation technician", "Gardener", "Machine operator", "Arborist", "Groundskeeper"]  
        position_menu = ctk.CTkOptionMenu(input_frame, variable=position_var, values=positions, width=150)
        position_menu.grid(row=0, column=0, padx=5, pady=(5, 10))
        
        date_entry = ctk.CTkEntry(input_frame, placeholder_text="MM-DD-YYYY", width=150)
        date_entry.grid(row=0, column=1, padx=5, pady=(5, 10))
        
        post_button = ctk.CTkButton(input_frame, text="Post Job", command=save_job, width=150)
        post_button.grid(row=0, column=2, padx=5, pady=(5, 10))
        
        posted_jobs_label = ctk.CTkLabel(frame, text="Posted Jobs:", anchor="w")
        posted_jobs_label.grid(row=3, column=0, padx=10, pady=(10, 5), sticky="w")
        
        job_listbox = Listbox(frame, height=8, font=("Arial", 16))
        job_listbox.grid(row=4, column=0, padx=10, pady=(5, 5), sticky="nsew")
        
        job_details_text = Text(frame, wrap="word", font=("Arial", 16), height=10, state="disabled")
        job_details_text.grid(row=5, column=0, padx=10, pady=(5, 10), sticky="nsew")

        def load_jobs():
            """Load and display the list of available job postings."""
            job_listbox.delete(0, 'end')
            try:
                jobs = Utils.load_json_from_s3("jobs.json")
                for job_id, job_info in jobs.items():
                    job_listbox.insert("end", f"{job_info['Job ID']} | {job_info['Date']} | {job_info['Position']}")
            except Exception:
                print("Error loading jobs data from S3.")
  
        def show_job_details(event):
            """Display detailed information about a selected job."""
            selected_index = job_listbox.curselection()
            if selected_index:
                job_id = job_listbox.get(selected_index).split(" | ")[0]
                try:
                    jobs = Utils.load_json_from_s3("jobs.json")
                    job_info = jobs.get(job_id)
                    if job_info:
                        job_details_text.config(state="normal")
                        job_details_text.delete("1.0", "end")
                        job_details_text.insert("end", f"Job ID: {job_info['Job ID']}\n")
                        job_details_text.insert("end", f"Date: {job_info['Date']}\n")
                        job_details_text.insert("end", f"Position: {job_info['Position']}\n")
                        job_details_text.insert("end", f"Description:\n{job_info['Job Description']}\n")
                        job_details_text.config(state="disabled")
                except Exception:
                    
                    print("Error loading job details from S3.")
        
        job_listbox.bind("<<ListboxSelect>>", show_job_details)

        load_jobs()
        
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_rowconfigure(4, weight=1)
        frame.grid_rowconfigure(5, weight=1)

    def init_completed_jobs_tab(self, frame):
        """Initialize the Completed Jobs tab content."""
        
        def load_completed_jobs():
            """Load and display the list of completed jobs."""
            job_listbox.delete(0, 'end')
            try:
                completed_jobs = Utils.load_json_from_s3("completed_jobs.json")
                for job_id, job_info in completed_jobs.items():
                    job_listbox.insert("end", f"{job_info['Job ID']} | {job_info['Date']} | {job_info['Position']}")
            except Exception:
                print("Error loading completed job postings from S3.")
        
        def show_job_details(event):
            """Display detailed information about a selected job."""
            selected_index = job_listbox.curselection()
            if selected_index:
                job_id = job_listbox.get(selected_index).split(" | ")[0]
                try:
                    completed_jobs = Utils.load_json_from_s3("completed_jobs.json")
                    job_info = completed_jobs.get(job_id)
                    if job_info:
                        job_details_text.config(state="normal")
                        job_details_text.delete("1.0", "end")
                        job_details_text.insert("end", f"Job ID: {job_info['Job ID']}\n")
                        job_details_text.insert("end", f"Date: {job_info['Date']}\n")
                        job_details_text.insert("end", f"Position: {job_info['Position']}\n")
                        job_details_text.insert("end", f"Description:\n{job_info['Job Description']}\n")
                        job_details_text.config(state="disabled")
                except Exception:
                    print("Error loading completed job postings from S3.")

        def view_selected_job_images(listbox):
            """Show images associated with the selected completed job."""
            selected_index = listbox.curselection()
            if selected_index:
                job_id = listbox.get(selected_index).split(" | ")[0]
                Utils.show_images(job_id, "completed_jobs.json", use_s3=True)
            else:
                messagebox.showwarning("No Selection", "Please select a job from the list.")
      
        job_listbox = Listbox(frame, height=8, font=("Arial", 16))
        job_listbox.grid(row=0, column=0, padx=10, pady=(10, 10), sticky="nsew")
        
        job_details_text = Text(frame, wrap="word", font=("Arial", 16), height=10, state="disabled")
        job_details_text.grid(row=2, column=0, padx=10, pady=(10, 10), sticky="nsew")
        
        view_images_button = ctk.CTkButton(frame, text="View Images", width=150, command=lambda: view_selected_job_images(job_listbox))
        view_images_button.grid(row=1, column=0, padx=5, pady=(10, 10))
        
        job_listbox.bind("<<ListboxSelect>>", show_job_details)
      
        load_completed_jobs()
        
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

    def init_inform_employee_tab(self, frame):
        """Initialize the Inform Employee tab content."""
        
        def load_employees():
            """Load employees from employees.json and display them in the listbox."""
            try:
                employees = Utils.load_json_from_s3("employees.json")
                return employees
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load employees: {e}")
                return {}
        
        def filter_employees():
            """Filter employees by the selected position and update the listbox."""
            selected_position = position_var.get()

            if selected_position == "Any Position":
                
                self.in_filtered_employees = self.employees
                all_employees_list = ["All Employees"] + [
                    f"{emp_id} | {emp_info.get('Name', 'Unknown')} | {emp_info.get('Position', 'N/A')}"
                    for emp_id, emp_info in self.employees.items()
                ]
            else:
                
                self.in_filtered_employees = {
                    emp_id: emp_info for emp_id, emp_info in self.employees.items()
                    if emp_info.get("Position") == selected_position
                }
                all_employees_list = [f"All {selected_position}s"] + [
                    f"{emp_id} | {emp_info.get('Name', 'Unknown')} | {emp_info.get('Position', 'N/A')}"
                    for emp_id, emp_info in self.in_filtered_employees.items()
                ]

            update_employee_listbox(all_employees_list)
        
        def update_employee_listbox(employees):
            """Update the employee listbox with the given data."""
            employee_listbox.delete(0, "end")
            for emp in employees:
                employee_listbox.insert("end", emp)
        
        def show_employee_info():
            """Show detailed information about the selected employee."""
            selected_index = employee_listbox.curselection()
            if selected_index:
                selected_id = employee_listbox.get(selected_index[0]).split(" | ")[0]
                employee = self.employees.get(selected_id)
                Utils.show_employee_info(employee, selected_id, self)
            else:
                messagebox.showwarning("No Selection", "Please select an employee from the list.")
        
        def send_message():
            """Send a message to the selected employee and save it to messages.json."""
            selected_index = employee_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("No Selection", "Please select an employee from the list.")
                return

            selected_item = employee_listbox.get(selected_index[0]).split(" | ")[0]
            message = message_text.get("1.0", "end").strip()
            date = date_entry.get().strip()

            if not message:
                messagebox.showwarning("No Message", "Please write a message before sending.")
                return
            if not date:
                messagebox.showwarning("No Date", "Please enter a date.")
                return

            try:
                messages = Utils.load_json_from_s3("messages.json")
            except Exception:
                messages = {}

            if selected_item == "All Employees":
                
                key = "All Employees" if position_var.get() == "Any Position" else position_var.get()
                if key not in messages:
                    messages[key] = []
                messages[key].append({"Message": message, "Date": date})
            else:
                
                selected_id = selected_item.split(" | ")[0]
                if selected_id not in messages:
                    messages[selected_id] = []
                messages[selected_id].append({"Message": message, "Date": date})

            try:
                Utils.save_json_to_s3(messages, "messages.json")
                messagebox.showinfo("Success", f"Message sent to successfully.")
                message_text.delete("1.0", "end")
                date_entry.delete(0, 'end')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send message: {e}")

            self.init_notifications_tab(self.view_notifications_frame)

        self.employees = load_employees()
        self.in_filtered_employees = self.employees

        listbox_frame = ctk.CTkFrame(frame, fg_color="transparent")
        listbox_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        listbox_frame.grid_columnconfigure(0, weight=1)
        listbox_frame.grid_rowconfigure(0, weight=1)

        employee_listbox = Listbox(listbox_frame, height=6, font=("Arial", 16))
        employee_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        all_employees_list = ["All Employees"] + [
            f"{emp_id} | {emp_info.get('Name', 'Unknown')} | {emp_info.get('Position', 'N/A')}"
            for emp_id, emp_info in self.employees.items()
        ]
        update_employee_listbox(all_employees_list)

        message_frame = ctk.CTkFrame(frame, fg_color="transparent")
        message_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        message_frame.grid_columnconfigure(0, weight=1)

        input_frame = ctk.CTkFrame(message_frame, fg_color="transparent")
        input_frame.grid(row=0, column=0, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_columnconfigure(1, weight=0)

        message_label = ctk.CTkLabel(input_frame, text="Write Message:", font=("Arial", 14), anchor="w")
        message_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        date_entry = ctk.CTkEntry(input_frame, placeholder_text="Enter Date (MM-DD-YYYY)", width=180)
        date_entry.grid(row=0, column=1, sticky="e", padx=5, pady=5)

        message_text = Text(message_frame, wrap="word", height=14, font=("Arial", 16), borderwidth=0, relief="flat")
        message_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        button_frame.grid_columnconfigure(3, weight=1)

        position_var = ctk.StringVar(value="Any Position")
        position_menu = ctk.CTkOptionMenu(
            button_frame,
            variable=position_var,
            values=["Any Position"] + list(set(emp.get("Position", "Unknown") for emp in self.employees.values())),
            width=150
        )
        position_menu.grid(row=0, column=0, padx=5, pady=5)

        search_button = ctk.CTkButton(button_frame, text="Search", command=filter_employees, width=120)
        search_button.grid(row=0, column=1, padx=5, pady=5)

        show_info_button = ctk.CTkButton(button_frame, text="Show Employee Info", command=show_employee_info, width=150)
        show_info_button.grid(row=0, column=2, padx=5, pady=5)

        send_button = ctk.CTkButton(button_frame, text="Send", command=send_message, width=120)
        send_button.grid(row=0, column=3, padx=5, pady=5)

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=0)
        frame.grid_rowconfigure(2, weight=0)

    def init_notifications_tab(self, frame):
        """Initialize the Notifications tab content for the Employer Dashboard."""
        notifications = []
        employee_name_map = {}

        def load_employee_names():
            """Load employee names from employees.json for mapping IDs to names."""
            nonlocal employee_name_map
            try:
                employees = Utils.load_json_from_s3("employees.json")
                employee_name_map = {emp_id: emp_info["Name"] for emp_id, emp_info in employees.items()}
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load employee names: {e}")
                employee_name_map = {}

        def load_messages():
            """Load all messages from messages.json."""
            nonlocal notifications

            
            try:
                all_messages = Utils.load_json_from_s3("messages.json")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load messages: {e}")
                all_messages = {}

            
            notifications.clear()
            for recipient, msgs in all_messages.items():
                recipient_name = (
                    employee_name_map.get(recipient, recipient)  
                    if recipient not in ["All Employees"] else recipient
                )
                for msg in msgs:
                    notifications.append({"To": recipient_name, "Message": msg["Message"], "Date": msg["Date"]})

            update_notifications_display()

        def update_notifications_display():
            """Display the loaded messages in the text frame."""
            notifications_text.config(state="normal")
            notifications_text.delete("1.0", "end")

            if not notifications:
                notifications_text.insert("end", "No notifications available.")
            else:
                for i, note in enumerate(notifications):
                    notifications_text.insert(
                        "end",
                        f"To: {note['To']}\nDate: {note['Date']}\nMessage:\n{note['Message']}\n\n"
                    )

                    
                    if i < len(notifications) - 1:
                        notifications_text.insert("end", "-" * 70 + "\n\n")

            notifications_text.config(state="disabled")

        
        notifications_label = ctk.CTkLabel(frame, text="Notifications:", font=("Arial", 14), anchor="w")
        notifications_label.grid(row=0, column=0, padx=10, pady=(5, 5), sticky="nw")

        notifications_text = Text(frame, wrap="word", font=("Arial", 16), state="disabled", height=20, borderwidth=0)
        notifications_text.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        
        load_employee_names()
        load_messages()

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=0)
        frame.grid_rowconfigure(1, weight=1)
    
    def logout(self):
        """Logout the current user and go back to the main menu."""
        self.controller.logout()

class EmployeeLogin(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.logged_in_employee = None 
        self.verification_code = None
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.show_login_window()

    def show_login_window(self):
        """Display the employee login window."""
        
        inner_frame = ctk.CTkFrame(self, width=350, height=200)
        inner_frame.grid(row=0, column=0, sticky="")
        inner_frame.grid_propagate(False)
        inner_frame.grid_columnconfigure(0, weight=1)
        inner_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(inner_frame, text="Employee Login", font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 20))
        
        email_label = ctk.CTkLabel(inner_frame, text="Email:")
        email_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.email_entry = ctk.CTkEntry(inner_frame, placeholder_text="Enter Email")
        self.email_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        password_label = ctk.CTkLabel(inner_frame, text="Password:")
        password_label.grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.password_entry = ctk.CTkEntry(inner_frame, placeholder_text="Enter Password", show="*")
        self.password_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        button_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        back_button = ctk.CTkButton(button_frame, text="Back", command=lambda: self.controller.show_frame("MainMenu"))
        back_button.grid(row=0, column=0, padx=(0, 10))

        login_button = ctk.CTkButton(button_frame, text="Login", command=self.login)
        login_button.grid(row=0, column=1)

    def login(self):
        """Handle the login process and verify employee credentials."""
        email = self.email_entry.get()
        password = self.password_entry.get()

        employee_data = self.validate_login(email, password)
        if employee_data:
            self.logged_employee_data = employee_data
            self.show_verification_window(email)
        else:
            messagebox.showerror("Login Failed", "Invalid email or password.")

    def validate_login(self, email, password):
        """Validate login by checking employees.json for matching email and password."""
        try:
            employees = Utils.load_json_from_s3("employees.json")
            for emp_id, emp_info in employees.items():
                if emp_info["Email"] == email and emp_info["Password"] == Utils.hash_password(password):
                    return emp_info
        except Exception:
            messagebox.showerror("Error", "Employee data not found or an error occurred.")
        return None
    
    def clear_inputs(self):
        """Clear the email and password input fields."""
        self.email_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')

    def send_verification_email(self, recipient):
        """Send a verification code to the user's email."""
        self.verification_code = str(random.randint(100000, 999999))  
        subject = "Your Verification Code"
        body = f"Your verification code for employee login is: {self.verification_code}"
        message = f"Subject: {subject}\n\n{body}"

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(Utils.SHARED_EMAIL, Utils.SHARED_PASSWORD)  
                server.sendmail(Utils.SHARED_EMAIL, recipient, message)  
        except Exception:
            pass

    def verify_code(self, entered_code, frame):
            """Verify the code entered by the user."""
            if entered_code == self.verification_code:
                self.clear_inputs()
                frame.destroy()
                self.controller.show_frame("EmployeeDashboard", employee_data=self.logged_employee_data)
            else:
                messagebox.showerror("Error", "Invalid verification code.")

    def show_verification_window(self, email):
        """Show the verification window where the user enters the code received via email."""
        self.send_verification_email(email)

        verification_frame = ctk.CTkFrame(self, width=350, height=200)
        verification_frame.grid(row=0, column=0, sticky="")
        verification_frame.grid_propagate(False)
        verification_frame.grid_columnconfigure(0, weight=1)
        verification_frame.grid_columnconfigure(1, weight=1)

        title_label = ctk.CTkLabel(verification_frame, text="Verify Your Account", font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 20))

        code_label = ctk.CTkLabel(verification_frame, text="Verification Code:")
        code_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        code_entry = ctk.CTkEntry(verification_frame, placeholder_text="Enter Code")
        code_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        info_label = ctk.CTkLabel(verification_frame, text=f"Verification code was sent to {email}.", font=("Arial", 10))
        info_label.grid(row=2, column=0, columnspan=2, pady=(5, 20))
        
        button_frame = ctk.CTkFrame(verification_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, columnspan=2, pady=5)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        back_button = ctk.CTkButton(button_frame, text="Back", command=lambda: self.show_login_window())
        back_button.grid(row=0, column=0, padx=(0, 10))
        
        verify_button = ctk.CTkButton(button_frame, text="Verify", command=lambda: self.verify_code(code_entry.get(), verification_frame))
        verify_button.grid(row=0, column=1)

class EmployerLogin(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
   
        inner_frame = ctk.CTkFrame(self, width=350, height=200)
        inner_frame.grid(row=0, column=0, sticky="")
        inner_frame.grid_propagate(False)
        inner_frame.grid_columnconfigure(0, weight=1)
        inner_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(inner_frame, text="Employer Login", font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 20))

        employer_id_label = ctk.CTkLabel(inner_frame, text="Employer ID:")
        employer_id_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.employer_id_entry = ctk.CTkEntry(inner_frame, placeholder_text="Enter Employer ID")
        self.employer_id_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        password_label = ctk.CTkLabel(inner_frame, text="Password:")
        password_label.grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.password_entry = ctk.CTkEntry(inner_frame, placeholder_text="Enter Password", show="*")
        self.password_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
 
        button_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        back_button = ctk.CTkButton(button_frame, text="Back", command=lambda: controller.show_frame("MainMenu"))
        back_button.grid(row=0, column=0, padx=(0, 10))

        login_button = ctk.CTkButton(button_frame, text="Login", command=self.login)
        login_button.grid(row=0, column=1)

    def login(self):
        employer_id = self.employer_id_entry.get()
        password = self.password_entry.get()

        if self.validate_login(employer_id, password):
            self.clear_inputs()
            self.controller.show_frame("EmployerDashboard")
        else:
            messagebox.showerror("Login Failed", "Invalid Employer ID or Password.")

    def validate_login(self, employer_id, password):
        """Validate login by checking employer.json for matching Employer ID and hashed password."""
        try:
            employers = Utils.load_json_from_s3("employer_login.json")
            if employer_id in employers:
                stored_hashed_password = employers[employer_id]["password"]
                return stored_hashed_password == Utils.hash_password(password)
        except Exception:
            
            messagebox.showerror("Error", "Employer data not found or an error occurred.")
        return False
    
    def clear_inputs(self):
        """Clear the email and password input fields."""
        self.employer_id_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')

class EmployeeRegister(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        inner_frame = ctk.CTkFrame(self)
        inner_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        inner_frame.grid_columnconfigure(0, weight=1)
        inner_frame.grid_columnconfigure(1, weight=1)

        self.employee_data = {}

        placeholder_img = Utils.round_image(Utils.resource_path("777.png"), size=(100, 100))
        self.photo = ctk.CTkImage(placeholder_img, size=(100, 100))
        
        self.image_label = ctk.CTkLabel(inner_frame, image=self.photo, text="", width=100, height=100)
        self.image_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        self.image_button = ctk.CTkButton(inner_frame, text="Select Image", command=self.select_image)
        self.image_button.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.fields = [
            ("Name", "Enter Full Name", Utils.validate_name),
            ("Address", "Enter Address", Utils.validate_address),
            ("Phone Number", "Enter Phone Number", Utils.validate_phone_number),
            ("Date of Birth", "MM-DD-YYYY", Utils.validate_date_of_birth),
            ("Skills", "Enter Skills (comma-separated)", Utils.validate_skills),
            ("Email", "Enter an active google email", Utils.validate_email),
            ("Password", "Enter Password (minimum 8 characters)", Utils.validate_password),
        ]

        self.entries = []
        for i, (label_text, placeholder, validator) in enumerate(self.fields, start=2):
            label = ctk.CTkLabel(inner_frame, text=label_text + ":", anchor="e", width=100)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="e")

            entry = ctk.CTkEntry(inner_frame, placeholder_text=placeholder, width=300)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="w")

            
            entry.bind("<FocusOut>", lambda e, v=validator, ent=entry: self.validate_input(v, ent))
            self.entries.append(entry)
        
        self.name_entry, self.address_entry, self.phone_entry, self.dob_entry, \
            self.skills_entry, self.email_entry, self.password_entry = self.entries

        position_label = ctk.CTkLabel(inner_frame, text="Select Position:", anchor="e", width=100)
        position_label.grid(row=len(self.fields) + 2, column=0, padx=10, pady=5, sticky="e")

        self.position_menu = ctk.CTkOptionMenu(
            inner_frame, values=["Assistant", "Foreman", "Mason", "Irrigation technician", "Gardener", "Machine operator", "Arborist", "Groundskeeper"], width=300
        )
        self.position_menu.grid(row=len(self.fields) + 2, column=1, padx=10, pady=5, sticky="w")
        self.position_menu.set("")

        button_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        button_frame.grid(row=len(self.fields) + 3, column=0, columnspan=2, pady=20)

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        go_back_button = ctk.CTkButton(button_frame, text="Go Back", command=lambda: self.controller.show_frame("MainMenu"), width=150)
        go_back_button.grid(row=0, column=0, padx=(0, 10))

        submit_button = ctk.CTkButton(button_frame, text="Submit", command=self.submit, width=150)
        submit_button.grid(row=0, column=1)

    def select_image(self):
        """Allow the user to select an image for their profile."""
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            img = Utils.round_image(file_path, size=(100, 100))
            self.photo = ctk.CTkImage(img, size=(100, 100))
            self.image_label.configure(image=self.photo, text="")
            self.employee_data["image"] = Utils.encode_image_to_base64(file_path)
        else:
            placeholder_img = Utils.round_image(Utils.resource_path("777.png"), size=(100, 100))
            self.photo = ctk.CTkImage(placeholder_img, size=(100, 100))
            self.image_label.configure(image=self.photo, text="")

    def validate_input(self, validator, entry):
        """Validate input and change entry field color."""
        if not validator(entry.get()):
            entry.configure(border_color="red") 
        else:
            entry.configure(border_color="green") 

    def clear_entries(self):
        """Clear all input fields and reset image to placeholder."""
        for entry in self.entries:
            entry.delete(0, "end")
            entry.configure(border_color="gray")
        self.position_menu.set("")
        placeholder_img = Utils.round_image(Utils.resource_path("777.png"), size=(100, 100))
        self.photo = ctk.CTkImage(placeholder_img, size=(100, 100))
        self.image_label.configure(image=self.photo, text="")

    def submit(self):
        """Submit the employee registration form."""
        if not Utils.validate_name(self.name_entry.get()):
            messagebox.showerror("Error", "Invalid Name. Only letters and spaces allowed.")
            return
        if not Utils.validate_address(self.address_entry.get()):
            messagebox.showerror("Error", "Invalid Address. Only letters, numbers, spaces, and commas allowed.")
            return
        if not Utils.validate_phone_number(self.phone_entry.get()):
            messagebox.showerror("Error", "Invalid Phone Number. Only 10 digits, spaces, and dashes allowed.")
            return
        if not Utils.validate_date_of_birth(self.dob_entry.get()):
            messagebox.showerror("Error", "Invalid Date of Birth. Use format MM-DD-YYYY.")
            return
        if not Utils.validate_skills(self.skills_entry.get()): 
            messagebox.showerror("Error", "Invalid Skills. Only letters, spaces, and commas allowed.")
            return
        if not Utils.validate_email(self.email_entry.get()):
            messagebox.showerror("Error", "Invalid Email. The email is either invalid or already in use.")
            return
        if not Utils.validate_password(self.password_entry.get()):
            messagebox.showerror("Error", "Invalid Password. Minimum 8 characters required.")
            return
        
        self.employee_data["Employee ID"] = f"{random.randint(100000, 999999)}"
        self.employee_data["Name"] = self.name_entry.get()
        self.employee_data["Address"] = self.address_entry.get()
        self.employee_data["Phone Number"] = Utils.format_phone_number(self.phone_entry.get())
        self.employee_data["Date of Birth"] = self.dob_entry.get()
        self.employee_data["Position"] = self.position_menu.get()
        self.employee_data["Skills"] = self.skills_entry.get()
        self.employee_data["Email"] = self.email_entry.get()
        self.employee_data["Password"] = Utils.hash_password(self.password_entry.get())

        all_data = Utils.load_json_from_s3("pending_employees.json")
        all_data[self.employee_data["Employee ID"]] = self.employee_data
        Utils.save_json_to_s3(all_data, "pending_employees.json")

        if "EmployerDashboard" in self.controller.frames:
            self.controller.frames["EmployerDashboard"].refresh()

        messagebox.showinfo("Success", "Registration successful! Awaiting approval.")
        self.clear_entries() 
        self.controller.show_frame("MainMenu")

class MainMenu(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
       
        image_path = Utils.resource_path("111.png") 
        background_image = Image.open(image_path).resize((1500, 600))
        self.bg_image = ctk.CTkImage(light_image=background_image, size=(1500, 600))

        self.bg_label = ctk.CTkLabel(self, image=self.bg_image, text="")
        self.bg_label.place(relwidth=1, relheight=1) 

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_columnconfigure(4, weight=1)
    
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1)

        toggle_button_frame = ctk.CTkFrame(self, width=50, height=50)
        toggle_button_frame.place(relx=0.98, rely=0.98, anchor="se") 
        toggle_button_frame.grid_propagate(False)

        inner_frame = ctk.CTkFrame(self, width=380, height=280, fg_color="transparent")
        inner_frame.grid(row=2, column=2, sticky="")
        inner_frame.grid_propagate(False)
        inner_frame.grid_columnconfigure(0, weight=1)
        inner_frame.grid_rowconfigure(1, weight=1)

        inner_frame = ctk.CTkFrame(self, fg_color="transparent")
        inner_frame.place(relx=0.5, rely=0.5, anchor="center") 


        self.title_label = ctk.CTkLabel(
            inner_frame, 
            text="Crosscut Landscaping \n Employee Management System", 
            font=("Arial", 20, "bold")
        )
        self.title_label.grid(row=0, column=0, pady=(10, 10), sticky="n")
        
        button_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        button_frame.grid(row=1, column=0, pady=10, sticky="n")

        button_frame.grid_columnconfigure(0, weight=1)

        employee_icon = ctk.CTkImage(Utils.round_image(Utils.resource_path("444.jpg"), size=(50, 50)))
        employer_icon = ctk.CTkImage(Utils.round_image(Utils.resource_path("666.jpg"), size=(50, 50)))
        register_icon = ctk.CTkImage(Utils.round_image(Utils.resource_path("888.jpg"), size=(50, 50)))

        self.employee_button = ctk.CTkButton(
            button_frame, 
            text="Employee Login", 
            image=employee_icon, 
            compound="left", 
            width=200, height=40, 
            corner_radius=10,
            command=lambda: self.controller.show_frame("EmployeeLogin")
        )
        self.employee_button.grid(row=0, column=0, pady=10)

        self.employer_button = ctk.CTkButton(
            button_frame, 
            text="Employer Login", 
            image=employer_icon, 
            compound="left", 
            width=200, height=40, 
            corner_radius=10,
            command=lambda: self.controller.show_frame("EmployerLogin")
        )
        self.employer_button.grid(row=1, column=0, pady=10)

        self.register_button = ctk.CTkButton(
            button_frame, 
            text="Employee Register", 
            image=register_icon, 
            compound="left", 
            width=200, height=40, 
            corner_radius=10, 
            command=lambda: self.controller.show_frame("EmployeeRegister")
        )
        self.register_button.grid(row=2, column=0, pady=10)

        ctk.set_default_color_theme("green")

        def toggle_mode():
            """Toggle between light and dark mode without window reinitialization."""
            current_mode = ctk.get_appearance_mode()
            new_mode = "Light" if current_mode == "Dark" else "Dark"
            ctk.set_appearance_mode(new_mode)

        toggle_button = ctk.CTkButton(
            toggle_button_frame,
            text="🌙",
            command=toggle_mode,
            width=40, height=40
        )
        toggle_button.grid(row=0, column=0, padx=5, pady=5)

class EmployeeManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Employee Management System")
        self.geometry("800x600")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.frames = {}
        
        for F in (MainMenu, EmployeeRegister, EmployerLogin, EmployerDashboard, EmployeeLogin):
            page_name = F.__name__
            frame = F(parent=self, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MainMenu")

    def show_frame(self, page_name, **kwargs):
        """Show a frame for the given page name, and recreate the frame if needed."""
        
        if page_name in ["EmployeeDashboard", "EmployerDashboard"]:
            if page_name in self.frames:
                
                self.frames[page_name].destroy()
                del self.frames[page_name]
            
            if page_name == "EmployeeDashboard" and "employee_data" in kwargs:
                frame = EmployeeDashboard(parent=self, controller=self, employee_data=kwargs["employee_data"])
            elif page_name == "EmployerDashboard":
                frame = EmployerDashboard(parent=self, controller=self)
            else:
                frame = self.frames[page_name]  

            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        else:
            frame = self.frames[page_name]

        frame.tkraise()

    def logout(self):
        """Resets the application state and navigates back to the main menu."""
        confirm = messagebox.askyesno("Logout", "Are you sure you want to log out?")
        if confirm:
            
            if "EmployeeDashboard" in self.frames:
                self.frames["EmployeeDashboard"].destroy()
                del self.frames["EmployeeDashboard"]

            if "EmployerDashboard" in self.frames:
                self.frames["EmployerDashboard"].destroy()
                del self.frames["EmployerDashboard"]

            self.show_frame("MainMenu")

if __name__ == "__main__":
    ctk.set_default_color_theme("green")
    app = EmployeeManagerApp()
    app.mainloop()