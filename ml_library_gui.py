import importlib
import io
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, StringVar, Text, Tk, filedialog, ttk
from tkinter import PhotoImage


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
        self.root.geometry("980x720")
        self.upload_paths = {}
        self.inputs = {}
        self.outputs = {}
        self.upload_labels = {}
        self.image_labels = {}
        self.image_references = {}

        notebook = ttk.Notebook(root)
        notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)

        for name, runner, sample, accepts_upload in TAB_CONFIGS:
            self._create_tab(notebook, name, runner, sample, accepts_upload)

    def _create_tab(self, notebook, name, runner, sample, accepts_upload):
        tab = ttk.Frame(notebook, padding=12)
        notebook.add(tab, text=name)

        ttk.Label(tab, text="Input").pack(anchor="w")
        input_box = Text(tab, height=8, wrap="word")
        input_box.insert("1.0", sample)
        input_box.pack(fill=BOTH, expand=False, pady=(4, 10))
        self.inputs[name] = input_box

        controls = ttk.Frame(tab)
        controls.pack(fill="x", pady=(0, 10))

        if accepts_upload:
            self.upload_paths[name] = None
            upload_text = StringVar(value="No dataset selected")
            self.upload_labels[name] = upload_text
            ttk.Button(
                controls,
                text="Upload Dataset",
                command=lambda tab_name=name: self._upload_file(tab_name),
            ).pack(side=LEFT)
            ttk.Label(controls, textvariable=upload_text).pack(side=LEFT, padx=10)

        ttk.Button(
            controls,
            text=f"Run {name}",
            command=lambda tab_name=name, tab_runner=runner: self._run_tab(
                tab_name, tab_runner
            ),
        ).pack(side=RIGHT)

        ttk.Label(tab, text="Output and final solution").pack(anchor="w")
        output_box = Text(tab, height=18, wrap="word")
        output_box.pack(fill=BOTH, expand=True, pady=(4, 0))
        self.outputs[name] = output_box

        ttk.Label(tab, text="Image preview").pack(anchor="w", pady=(10, 0))
        image_label = ttk.Label(tab, text="No image output for this run.")
        image_label.pack(fill=BOTH, expand=False, pady=(4, 0))
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
        text = self.inputs[name].get("1.0", END)
        output_box = self.outputs[name]
        output_box.delete("1.0", END)
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

        image = PhotoImage(file=image_path)
        self.image_references[name] = image
        image_label.configure(image=image, text="")


def main():  # pragma: no cover - interactive Tkinter UI
    root = Tk()
    MachineLearningLibraryApp(root)
    root.mainloop()


if __name__ == "__main__":  # pragma: no cover - interactive Tkinter UI
    main()
