from base import SortingAlgorithm
from typing import List, Dict, Tuple

class QuickSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("Quick Sort")

    def sort(self, arr: List[int]) -> Tuple[List[int], int, int]:
        comparisons = [0]
        swaps = [0]
        
        def partition(low: int, high: int) -> int:
            pivot = arr[high]
            i = low - 1
            
            for j in range(low, high):
                comparisons[0] += 1
                if arr[j] <= pivot:
                    i += 1
                       
                    arr[i], arr[j] = arr[j], arr[i]
                    swaps[0] += 1
                    
                
            arr[i + 1], arr[high] = arr[high], arr[i + 1]
            swaps[0] += 1
            return i + 1
        
        def quick_sort_rec(low: int, high: int):
            if low < high:
                pi = partition(low, high)
                quick_sort_rec(low, pi - 1)
                quick_sort_rec(pi + 1, high)
                
        if len(arr) > 1:
            quick_sort_rec(0, len(arr) - 1)
            
        return arr, comparisons[0], swaps[0]
    
    def get_time_complexity(self) -> Dict[str, str]:
        return {
            "best": "O(n log n)",
            "average": "O(n log n)",
            "worst": "O(n^2)"  
        }
        
    def get_space_complexity(self) -> str:
        return "O(log n)"
