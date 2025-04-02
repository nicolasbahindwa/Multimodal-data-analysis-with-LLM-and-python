from mcp.server.fastmcp import FastMCP
import numpy as np
import json

# MPC server instance name "DataAnalysis"
mcp = FastMCP("DataAnalysis")

@mcp.tool()
def calculate_statistics(data: list) -> str:
    """
    Calculate basic statistics for a dataset
    
    Args:
        data: A list of numerical values
        
    Returns:
        A string containing basic statistics
    """
    # Convert to numpy array for calculations
    try:
        arr = np.array(data, dtype=float)
        
        # Calculate basic statistics
        result = {
            "count": len(arr),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "std_dev": float(np.std(arr)),
            "variance": float(np.var(arr)),
            "sum": float(np.sum(arr))
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error analyzing data: {str(e)}"

@mcp.tool()
def calculate_correlation(data_x: list, data_y: list) -> str:
    """
    Calculate correlation between two datasets
    
    Args:
        data_x: First list of numerical values
        data_y: Second list of numerical values
        
    Returns:
        Correlation coefficient and p-value
    """
    try:
        if len(data_x) != len(data_y):
            return "Error: Both datasets must have the same length"
            
        arr_x = np.array(data_x, dtype=float)
        arr_y = np.array(data_y, dtype=float)
        
        correlation = np.corrcoef(arr_x, arr_y)[0, 1]
        
        return f"Correlation coefficient: {correlation:.4f}"
    except Exception as e:
        return f"Error calculating correlation: {str(e)}"

@mcp.tool()
def find_outliers(data: list, method: str = "zscore") -> str:
    """
    Find outliers in a dataset
    
    Args:
        data: List of numerical values
        method: Method to use for outlier detection ("zscore" or "iqr")
        
    Returns:
        Indices and values of outliers
    """
    try:
        arr = np.array(data, dtype=float)
        outliers = []
        outlier_indices = []
        
        if method.lower() == "zscore":
            # Z-score method (values more than 2.5 standard deviations away)
            mean = np.mean(arr)
            std = np.std(arr)
            threshold = 2.5
            
            for i, value in enumerate(arr):
                z_score = abs((value - mean) / std)
                if z_score > threshold:
                    outliers.append(float(value))
                    outlier_indices.append(i)
                    
        elif method.lower() == "iqr":
            # IQR method
            q1 = np.percentile(arr, 25)
            q3 = np.percentile(arr, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            for i, value in enumerate(arr):
                if value < lower_bound or value > upper_bound:
                    outliers.append(float(value))
                    outlier_indices.append(i)
        else:
            return f"Error: Unknown method '{method}'. Use 'zscore' or 'iqr'."
            
        result = {
            "outlier_count": len(outliers),
            "outlier_indices": outlier_indices,
            "outlier_values": outliers,
            "method": method
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error finding outliers: {str(e)}"

# Run the MCP server
if __name__ == '__main__':
    mcp.run()