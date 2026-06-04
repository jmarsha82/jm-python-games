import importlib
import io
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image


DEFAULT_NUMBERS = "1, 2, 3, 4, 5"
DEFAULT_CSV = "feature,target\n1,2\n2,4\n3,6\n4,8\n5,10\n"
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "python_ml_library_gui_mpl")
)
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "1")


@dataclass(frozen=True)
class RunResult:
    text: str
    image_path: Path | None = None


def parse_numbers(text):
    values = [part.strip() for part in text.replace("\n", ",").split(",")]
    numbers = [float(value) for value in values if value]
    if not numbers:
        raise ValueError("Enter at least one number separated by commas.")
    return numbers


def load_library(module_name, install_name=None):
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        package = install_name or module_name
        raise RuntimeError(
            f"{package} is not installed. Run: pip install -r requirements.txt"
        ) from exc


def dataframe_from_input(text, upload_path=None, pandas_module=None):
    pd = pandas_module or load_library("pandas")
    if upload_path:
        path = Path(upload_path)
        suffix = path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(path)
        if suffix in {".tsv", ".txt"}:
            return pd.read_csv(path, sep="\t")
        if suffix == ".json":
            return pd.read_json(path)
        if suffix in {".xls", ".xlsx"}:
            return pd.read_excel(path)
        raise ValueError("Supported uploads: .csv, .tsv, .txt, .json, .xls, .xlsx")

    csv_text = text.strip() or DEFAULT_CSV
    return pd.read_csv(io.StringIO(csv_text))


def save_plot(fig, prefix):
    output_dir = Path(tempfile.gettempdir()) / "python_ml_library_gui"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{prefix}.png"
    fig.savefig(output_path, bbox_inches="tight")
    return output_path


def result_text(result):
    if isinstance(result, RunResult):
        return result.text
    return str(result)


def result_image_path(result):
    if isinstance(result, RunResult) and result.image_path:
        return Path(result.image_path)
    return None


def scaled_preview_size(image_size, max_size=(620, 340)):
    width, height = image_size
    max_width, max_height = max_size
    if width <= 0 or height <= 0:
        raise ValueError("Image dimensions must be positive.")
    scale = min(max_width / width, max_height / height, 1)
    return int(width * scale), int(height * scale)


def run_numpy_demo(text, np_module=None):
    np = np_module or load_library("numpy")
    array = np.array(parse_numbers(text or DEFAULT_NUMBERS), dtype=float)
    squared = array**2
    return (
        "NumPy array operations\n"
        f"Input array: {array.tolist()}\n"
        f"Squared values: {squared.tolist()}\n"
        f"Mean: {float(np.mean(array)):.4f}\n"
        f"Standard deviation: {float(np.std(array)):.4f}\n\n"
        f"Final solution: NumPy processed {array.size} numeric values."
    )


def run_pandas_demo(text, upload_path=None, pandas_module=None):
    df = dataframe_from_input(text, upload_path, pandas_module)
    summary = df.describe(include="all").to_string()
    return (
        "Pandas dataframe analysis\n"
        f"Rows: {len(df)}\n"
        f"Columns: {', '.join(str(column) for column in df.columns)}\n\n"
        f"Head:\n{df.head().to_string(index=False)}\n\n"
        f"Summary:\n{summary}\n\n"
        "Final solution: Pandas loaded the dataset and produced a tabular summary."
    )


def run_matplotlib_demo(text, mpl_module=None, np_module=None):
    np = np_module or load_library("numpy")
    matplotlib = mpl_module or load_library("matplotlib")
    matplotlib.use("Agg")
    pyplot = load_library("matplotlib.pyplot")
    values = np.array(parse_numbers(text or DEFAULT_NUMBERS), dtype=float)
    fig, ax = pyplot.subplots(figsize=(5, 3))
    ax.plot(range(1, len(values) + 1), values, marker="o")
    ax.set_title("Matplotlib Line Plot")
    ax.set_xlabel("Index")
    ax.set_ylabel("Value")
    output_path = save_plot(fig, "matplotlib_output")
    pyplot.close(fig)
    return RunResult(
        "Matplotlib visualization\n"
        f"Values plotted: {values.tolist()}\n"
        f"Chart saved to: {output_path}\n\n"
        "Final solution: Matplotlib generated a line chart from the input values.",
        output_path,
    )


def run_seaborn_demo(text, upload_path=None, seaborn_module=None, pandas_module=None):
    sns = seaborn_module or load_library("seaborn")
    matplotlib = load_library("matplotlib")
    matplotlib.use("Agg")
    pyplot = load_library("matplotlib.pyplot")
    df = dataframe_from_input(text, upload_path, pandas_module)
    numeric_columns = list(df.select_dtypes(include="number").columns)
    if len(numeric_columns) < 2:
        raise ValueError("Seaborn needs at least two numeric columns.")
    fig = pyplot.figure(figsize=(5, 3))
    sns.scatterplot(data=df, x=numeric_columns[0], y=numeric_columns[1])
    pyplot.title("Seaborn Scatter Plot")
    output_path = save_plot(fig, "seaborn_output")
    pyplot.close(fig)
    return RunResult(
        "Seaborn visualization\n"
        f"X column: {numeric_columns[0]}\n"
        f"Y column: {numeric_columns[1]}\n"
        f"Chart saved to: {output_path}\n\n"
        "Final solution: Seaborn generated a statistical scatter plot.",
        output_path,
    )


def run_sklearn_demo(text, upload_path=None, pandas_module=None):
    pd = pandas_module or load_library("pandas")
    linear_model = load_library("sklearn.linear_model", "scikit-learn")
    df = dataframe_from_input(text, upload_path, pd)
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.shape[1] < 2:
        raise ValueError("Scikit-learn needs at least two numeric columns.")
    feature_name = numeric_df.columns[0]
    target_name = numeric_df.columns[1]
    x = numeric_df[[feature_name]]
    y = numeric_df[target_name]
    model = linear_model.LinearRegression()
    model.fit(x, y)
    next_value = float(x.iloc[-1, 0]) + 1
    prediction = float(model.predict(pd.DataFrame({feature_name: [next_value]}))[0])
    return (
        "Scikit-learn linear regression\n"
        f"Feature column: {feature_name}\n"
        f"Target column: {target_name}\n"
        f"Coefficient: {float(model.coef_[0]):.4f}\n"
        f"Intercept: {float(model.intercept_):.4f}\n"
        f"Prediction for {feature_name}={next_value:.4f}: {prediction:.4f}\n\n"
        "Final solution: Scikit-learn fit a regression model and made a prediction."
    )


def run_pytorch_demo(text, torch_module=None):
    torch = torch_module or load_library("torch")
    tensor = torch.tensor(parse_numbers(text or DEFAULT_NUMBERS), dtype=torch.float32)
    normalized = (tensor - tensor.mean()) / tensor.std(unbiased=False)
    return (
        "PyTorch tensor operations\n"
        f"Input tensor: {tensor.tolist()}\n"
        f"Normalized tensor: {normalized.tolist()}\n"
        f"Tensor sum: {float(tensor.sum()):.4f}\n\n"
        "Final solution: PyTorch converted the values into a tensor and normalized them."
    )


def run_keras_demo(text):
    np = load_library("numpy")
    try:
        keras = load_library("keras")
    except RuntimeError:
        tensorflow = load_library("tensorflow")
        keras = tensorflow.keras
    values = np.array(parse_numbers(text or DEFAULT_NUMBERS), dtype="float32").reshape(-1, 1)
    model = keras.Sequential(
        [
            keras.layers.Input(shape=(1,)),
            keras.layers.Dense(1, kernel_initializer="ones", bias_initializer="zeros"),
        ]
    )
    predictions = model.predict(values, verbose=0).flatten().tolist()
    return (
        "Keras neural network inference\n"
        f"Input values: {values.flatten().tolist()}\n"
        f"Predictions from a one-layer demo model: {predictions}\n\n"
        "Final solution: Keras built a tiny model and ran inference."
    )


def run_tensorflow_demo(text):
    tf = load_library("tensorflow")
    tensor = tf.constant(parse_numbers(text or DEFAULT_NUMBERS), dtype=tf.float32)
    squared = tf.square(tensor)
    mean = tf.reduce_mean(tensor)
    return (
        "TensorFlow tensor operations\n"
        f"Input tensor: {tensor.numpy().tolist()}\n"
        f"Squared tensor: {squared.numpy().tolist()}\n"
        f"Mean: {float(mean.numpy()):.4f}\n\n"
        "Final solution: TensorFlow executed tensor math on the input values."
    )


TAB_CONFIGS = [
    ("NumPy", run_numpy_demo, DEFAULT_NUMBERS, False),
    ("Pandas", run_pandas_demo, DEFAULT_CSV, True),
    ("Matplotlib", run_matplotlib_demo, DEFAULT_NUMBERS, False),
    ("Seaborn", run_seaborn_demo, DEFAULT_CSV, True),
    ("Scikit-learn", run_sklearn_demo, DEFAULT_CSV, True),
    ("PyTorch", run_pytorch_demo, DEFAULT_NUMBERS, False),
    ("Keras", run_keras_demo, DEFAULT_NUMBERS, False),
    ("TensorFlow", run_tensorflow_demo, DEFAULT_NUMBERS, False),
]


class MachineLearningLibraryApp:  # pragma: no cover - interactive Tkinter UI
    def __init__(self, root):
        self.root = root
        self.root.title("Python Machine Learning Library Runner")
        self.root.geometry("1180x820")
        self.root.minsize(980, 700)
        self.upload_paths = {}
        self.inputs = {}
        self.outputs = {}
        self.upload_labels = {}
        self.image_labels = {}
        self.image_references = {}

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        shell = ctk.CTkFrame(root, fg_color="#0f172a", corner_radius=0)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(shell, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 8))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Machine Learning Library Runner",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#f8fafc",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Run focused Python ML demos, inspect text output, and preview generated charts.",
            font=ctk.CTkFont(size=14),
            text_color="#94a3b8",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        tabview = ctk.CTkTabview(
            shell,
            fg_color="#111827",
            segmented_button_fg_color="#1e293b",
            segmented_button_selected_color="#2563eb",
            segmented_button_selected_hover_color="#1d4ed8",
            segmented_button_unselected_color="#334155",
            segmented_button_unselected_hover_color="#475569",
            corner_radius=8,
        )
        tabview.grid(row=1, column=0, sticky="nsew", padx=22, pady=(8, 22))

        for name, runner, sample, accepts_upload in TAB_CONFIGS:
            self._create_tab(tabview, name, runner, sample, accepts_upload)

    def _create_tab(self, tabview, name, runner, sample, accepts_upload):
        tabview.add(name)
        tab = tabview.tab(name)
        tab.configure(fg_color="#111827")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        input_panel = ctk.CTkFrame(tab, fg_color="#1f2937", corner_radius=8)
        input_panel.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=12)
        input_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            input_panel,
            text=f"{name} input",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#e5e7eb",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))
        input_box = ctk.CTkTextbox(
            input_panel,
            height=135,
            wrap="word",
            border_width=1,
            border_color="#334155",
            fg_color="#0f172a",
            text_color="#e5e7eb",
        )
        input_box.insert("1.0", sample)
        input_box.grid(row=1, column=0, sticky="ew", padx=14, pady=(4, 12))
        self.inputs[name] = input_box

        controls = ctk.CTkFrame(input_panel, fg_color="transparent")
        controls.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        controls.grid_columnconfigure(1, weight=1)

        if accepts_upload:
            self.upload_paths[name] = None
            upload_text = ctk.StringVar(value="No dataset selected")
            self.upload_labels[name] = upload_text
            ctk.CTkButton(
                controls,
                text="Upload Dataset",
                command=lambda tab_name=name: self._upload_file(tab_name),
                width=150,
                fg_color="#0f766e",
                hover_color="#115e59",
            ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(
                controls,
                textvariable=upload_text,
                text_color="#cbd5e1",
                anchor="w",
            ).grid(row=0, column=1, sticky="ew", padx=12)

        ctk.CTkButton(
            controls,
            text=f"Run {name}",
            command=lambda tab_name=name, tab_runner=runner: self._run_tab(
                tab_name, tab_runner
            ),
            height=36,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
        ).grid(row=0, column=2, sticky="e")

        output_panel = ctk.CTkFrame(tab, fg_color="#1f2937", corner_radius=8)
        output_panel.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(0, 12))
        output_panel.grid_columnconfigure(0, weight=1)
        output_panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            output_panel,
            text="Output and final solution",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#e5e7eb",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))
        output_box = ctk.CTkTextbox(
            output_panel,
            wrap="word",
            border_width=1,
            border_color="#334155",
            fg_color="#0f172a",
            text_color="#e5e7eb",
        )
        output_box.grid(row=1, column=0, sticky="nsew", padx=14, pady=(4, 14))
        self.outputs[name] = output_box

        image_panel = ctk.CTkFrame(tab, fg_color="#1f2937", corner_radius=8)
        image_panel.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=(0, 12))
        image_panel.grid_columnconfigure(0, weight=1)
        image_panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            image_panel,
            text="Image preview",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#e5e7eb",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))
        image_label = ctk.CTkLabel(
            image_panel,
            text="No image output for this run.",
            text_color="#94a3b8",
            fg_color="#0f172a",
            corner_radius=8,
        )
        image_label.grid(row=1, column=0, sticky="nsew", padx=14, pady=(4, 14))
        self.image_labels[name] = image_label

    def _upload_file(self, name):
        path = filedialog.askopenfilename(
            title=f"Select dataset for {name}",
            filetypes=[
                ("Supported datasets", "*.csv *.tsv *.txt *.json *.xls *.xlsx"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.upload_paths[name] = path
            self.upload_labels[name].set(path)

    def _run_tab(self, name, runner):
        text = self.inputs[name].get("1.0", "end")
        output_box = self.outputs[name]
        output_box.delete("1.0", "end")
        try:
            upload_path = self.upload_paths.get(name)
            if upload_path is not None:
                result = runner(text, upload_path=upload_path)
            else:
                result = runner(text)
        except Exception as exc:
            result = f"Error running {name}:\n{exc}"
        output_box.insert("1.0", result_text(result))
        self._show_image_result(name, result_image_path(result))

    def _show_image_result(self, name, image_path):
        image_label = self.image_labels[name]
        if not image_path:
            self.image_references.pop(name, None)
            image_label.configure(image="", text="No image output for this run.")
            return

        pil_image = Image.open(image_path)
        image = ctk.CTkImage(
            light_image=pil_image,
            dark_image=pil_image,
            size=scaled_preview_size(pil_image.size),
        )
        self.image_references[name] = image
        image_label.configure(image=image, text="")


def main():  # pragma: no cover - interactive Tkinter UI
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    MachineLearningLibraryApp(root)
    root.mainloop()


if __name__ == "__main__":  # pragma: no cover - interactive Tkinter UI
    main()
