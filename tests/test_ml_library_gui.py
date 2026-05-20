import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import ml_library_gui as app


class ParseNumbersTests(unittest.TestCase):
    def test_parse_numbers_accepts_commas_and_newlines(self):
        self.assertEqual(app.parse_numbers("1, 2\n3"), [1.0, 2.0, 3.0])

    def test_parse_numbers_requires_at_least_one_number(self):
        with self.assertRaisesRegex(ValueError, "at least one number"):
            app.parse_numbers(" , \n ")


class DependencyTests(unittest.TestCase):
    def test_load_library_explains_missing_dependency(self):
        with patch("importlib.import_module", side_effect=ImportError("missing")):
            with self.assertRaisesRegex(RuntimeError, "pip install -r requirements.txt"):
                app.load_library("missing_package")


class DemoOutputTests(unittest.TestCase):
    def test_numpy_demo_returns_final_solution(self):
        class FakeArray(list):
            @property
            def size(self):
                return len(self)

            def __pow__(self, power):
                return FakeArray([value**power for value in self])

            def tolist(self):
                return list(self)

        class FakeNumpy:
            @staticmethod
            def array(values, dtype=float):
                return FakeArray(values)

            @staticmethod
            def mean(values):
                return sum(values) / len(values)

            @staticmethod
            def std(values):
                mean = FakeNumpy.mean(values)
                return (sum((value - mean) ** 2 for value in values) / len(values)) ** 0.5

        self.assertIn("Final solution", app.run_numpy_demo("1,2,3", FakeNumpy))

    def test_pandas_demo_reads_inline_csv(self):
        result = app.run_pandas_demo("feature,target\n1,2\n2,4\n")
        self.assertIn("Rows: 2", result)
        self.assertIn("Final solution", result)

    def test_dataframe_from_input_reads_upload(self):
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.csv"
            path.write_text("feature,target\n1,2\n", encoding="utf-8")
            dataframe = app.dataframe_from_input("", upload_path=path)

        self.assertEqual(list(dataframe.columns), ["feature", "target"])

    def test_dataframe_from_input_rejects_unknown_upload_type(self):
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.unsupported"
            path.write_text("feature,target\n1,2\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Supported uploads"):
                app.dataframe_from_input("", upload_path=path)

    def test_matplotlib_demo_saves_chart(self):
        result = app.run_matplotlib_demo("1,2,3")
        self.assertIn("Chart saved to:", result.text)
        self.assertIn("Final solution", result.text)
        self.assertTrue(result.image_path.exists())
        self.assertEqual(app.result_image_path(result), result.image_path)

    def test_seaborn_demo_saves_chart(self):
        result = app.run_seaborn_demo("feature,target\n1,2\n2,4\n3,6\n")
        self.assertIn("X column: feature", result.text)
        self.assertIn("Final solution", result.text)
        self.assertTrue(result.image_path.exists())

    def test_result_helpers_handle_text_only_output(self):
        self.assertEqual(app.result_text("plain output"), "plain output")
        self.assertIsNone(app.result_image_path("plain output"))

    def test_seaborn_demo_requires_two_numeric_columns(self):
        with self.assertRaisesRegex(ValueError, "two numeric columns"):
            app.run_seaborn_demo("name\nalpha\nbeta\n")

    def test_sklearn_demo_fits_regression(self):
        result = app.run_sklearn_demo("feature,target\n1,2\n2,4\n3,6\n")
        self.assertIn("Coefficient:", result)
        self.assertIn("Final solution", result)

    def test_sklearn_demo_requires_two_numeric_columns(self):
        with self.assertRaisesRegex(ValueError, "two numeric columns"):
            app.run_sklearn_demo("feature\n1\n2\n")

    def test_pytorch_demo_runs_tensor_math(self):
        result = app.run_pytorch_demo("1,2,3")
        self.assertIn("Normalized tensor:", result)
        self.assertIn("Final solution", result)

    def test_keras_demo_runs_inference(self):
        result = app.run_keras_demo("1,2")
        self.assertIn("Predictions from a one-layer demo model:", result)
        self.assertIn("Final solution", result)

    def test_tensorflow_demo_runs_tensor_math(self):
        result = app.run_tensorflow_demo("1,2,3")
        self.assertIn("Squared tensor:", result)
        self.assertIn("Final solution", result)


if __name__ == "__main__":
    unittest.main()
