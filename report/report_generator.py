import argparse
import os
import sys
from matplotlib import pyplot as plt
import pandas as pd


class ReportGenerator:
    def __init__(self, input_path: str = ".", output_path: str = "."):
        """
        Initializes the ReportGenerator with input and output paths.

        Parameters:
        - input_path (str): The path to the
          directory or CSV file containing the input data.
        - output_path (str): The directory where the reports will be saved.
        """
        self.input_path = input_path
        self.output_path = output_path

    def _find_project_details(self):
        """
        Checks if the input path is the 'project_details'
        folder or contains it.
        If found, gathers all CSV files for processing.

        Returns:
        - list: A list of CSV file paths within the
         'project_details' directory.
        """
        # Check if the input path is directly the `project_details` folder
        if os.path.basename(
            self.input_path
        ) == "project_details" and os.path.isdir(self.input_path):
            project_details_path = self.input_path
        else:
            # Search for a `project_details` folder inside the input path
            project_details_path = os.path.join(
                self.input_path, "project_details"
            )
            if not os.path.isdir(project_details_path):
                raise FileNotFoundError(
                    f"'project_details' folder not found in {self.input_path}."
                )

        # Gather all CSV files in the folder
        csv_files = [
            os.path.join(project_details_path, f)
            for f in os.listdir(project_details_path)
            if f.endswith(".csv")
        ]
        if not csv_files:
            raise FileNotFoundError(
                f"No CSV files found in {project_details_path}."
            )
        return csv_files

    def _load_data(self, file_paths):
        """
        Loads data from multiple CSV files into a single DataFrame.

        Parameters:
        - file_paths (list): List of file paths to load.

        Returns:
        - pd.DataFrame: A DataFrame containing all the merged data.
        """
        dfs = []
        for file in file_paths:
            print(f"Loading file: {file}")
            dfs.append(pd.read_csv(file))
        return pd.concat(dfs, ignore_index=True)

    def smell_report(self, df):
        """Generates a general overview report."""
        report = (
            df.groupby("smell_name")["filename"]
            .count()
            .rename("occurrences")
            .reset_index()
        )
        report.to_csv(
            os.path.join(self.output_path, "general_overview.csv"), index=False
        )
        print("General smell report saved to 'general_overview.csv'.")

    def project_report(self, df):
        """
        Generates a project-specific report
        treating files as part of separate projects.
        """
        # Extract project names from file paths
        df["project_name"] = df["filename"].apply(
            lambda x: os.path.basename(os.path.dirname(x)) or "root"
        )
        report = (
            df.groupby("project_name")["smell_name"]
            .count()
            .rename("total_smells")
            .reset_index()
        )
        output_file = os.path.join(self.output_path, "project_overview.csv")
        report.to_csv(output_file, index=False)
        print(f"Project-specific report saved to '{output_file}'.")

    def summary_report(self, df):
        """
        Generates a summary report with:
        - General overview of code smells.
        - Per-project summary of total smells and density.
        - Detailed sheets for each project (smells and file analysis).
        """
        df["project_name"] = df["filename"].apply(
            lambda x: os.path.basename(os.path.dirname(x)) or "root"
        )
        general_report = (
            df.groupby("smell_name")["filename"]
            .count()
            .rename("occurrences")
            .reset_index()
        )
        
        project_summary_smells = (
            df.groupby("project_name")["smell_name"]
            .count()
            .rename("total_smells")
            .reset_index()
        )

        if "loc" in df.columns:
            unique_files = df.drop_duplicates(subset=["filename"])
            project_loc = unique_files.groupby("project_name")["loc"].sum().rename("total_loc").reset_index()
            project_summary = pd.merge(project_summary_smells, project_loc, on="project_name", how="left")
            project_summary["density"] = project_summary["total_smells"] / project_summary["total_loc"]
        else:
            project_summary = project_summary_smells

        output_file = os.path.join(self.output_path, "summary_report.xlsx")
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            general_report.to_excel(
                writer, sheet_name="General Overview", index=False
            )
            project_summary.to_excel(
                writer, sheet_name="Project Overview", index=False
            )
            for project_name, project_df in df.groupby("project_name"):
                details = (
                    project_df.groupby("smell_name")["filename"]
                    .count()
                    .rename("occurrences")
                    .reset_index()
                )
                sanitized_name = project_name[:30]
                details.to_excel(
                    writer, sheet_name=sanitized_name, index=False
                )
                
                if "loc" in project_df.columns:
                    file_stats = project_df.groupby("filename").agg({
                        "smell_name": "count",
                        "loc": "first"
                    }).reset_index()
                    file_stats.rename(columns={"smell_name": "smells"}, inplace=True)
                    file_stats["density"] = file_stats["smells"] / file_stats["loc"]
                    
                    def classify(d):
                        if pd.isna(d): return "Unknown"
                        if d < 0.005: return "Low"
                        elif d < 0.05: return "Medium"
                        else: return "High"
                    
                    file_stats["quality"] = file_stats["density"].apply(classify)
                    file_stats["short_filename"] = file_stats["filename"].apply(os.path.basename)
                    
                    file_stats = file_stats[["short_filename", "smells", "loc", "density", "quality", "filename"]]
                    
                    files_sheet_name = (project_name[:24] + "_Files")[:31]
                    file_stats.to_excel(writer, sheet_name=files_sheet_name, index=False)
        
        print(f"Summary report saved to '{output_file}'.")

    def visualize_smell_report(self, df):
        """Generates a bar chart for the general smell overview."""
        report = (
            df.groupby("smell_name")["filename"]
            .count()
            .rename("occurrences")
            .reset_index()
        )
        report.plot(kind="bar", x="smell_name", y="occurrences", legend=False)
        plt.title("Smell Occurrences by Type")
        plt.xlabel("Smell Type")
        plt.ylabel("Number of Occurrences")
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_path, "smell_report_chart.png"))
        print("Bar chart saved to 'smell_report_chart.png'.")

    def menu(self):
        """Displays a menu for the user to choose which report to generate."""
        print("Select which reports to generate:")
        print("1. General Smell Report")
        print("2. Project-Specific Report")
        print("3. Both Reports")
        print("4. Plot Report")
        print("5. Summary .xlsx Report")
        print("6. Exit")
        choice = input("Enter your choice: ")
        return choice

    def run(self):
        """
        Main execution logic for the report generation process.
        Handles user input and orchestrates report generation.
        """
        try:
            csv_files = self._find_project_details()
            
            metric_files = [f for f in csv_files if "_metrics.csv" in f or "file_metrics.csv" in f]
            result_files = [f for f in csv_files if f not in metric_files]
            
            df = pd.DataFrame()
            df_results = pd.DataFrame()
            df_metrics = pd.DataFrame()

            if result_files:
                df_results = self._load_data(result_files)
            
            if metric_files:
                df_metrics = self._load_data(metric_files)
                if not df_metrics.empty:
                    df_metrics.drop_duplicates(subset=['filename'], inplace=True)
            
            if not df_metrics.empty and not df_results.empty:
                df = pd.merge(df_metrics, df_results, on="filename", how="left")
            elif not df_results.empty:
                df = df_results
            elif not df_metrics.empty:
                df = df_metrics
                # Ensure smell columns exist for compatibility
                for col in ["smell_name", "function_name", "project_name"]:
                    if col not in df.columns:
                        df[col] = None
            else:
                print("No data found to generate reports.")
                return

            choice = self.menu()
            if choice == "1":
                self.smell_report(df)
            elif choice == "2":
                self.project_report(df)
            elif choice == "3":
                self.smell_report(df)
                self.project_report(df)
            elif choice == "4":
                self.visualize_smell_report(df)
            elif choice == "5":
                self.summary_report(df)
            elif choice == "6":
                print("Exiting...")
            else:
                print("Invalid choice. Exiting.")
        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        description="Generate reports for code smell analysis."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input directory or file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Directory to save the reports.",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print(f"Error: Input path '{args.input}' is not a valid directory.")
        sys.exit(1)

    if not os.path.isdir(args.output):
        os.makedirs(args.output, exist_ok=True)

    generator = ReportGenerator(input_path=args.input, output_path=args.output)
    generator.run()


if __name__ == "__main__":
    main()
