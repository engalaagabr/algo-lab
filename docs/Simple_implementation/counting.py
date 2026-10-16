from base import SortingAlgorithm
from typing import List, Dict, Tuple

class CountingSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("Counting Sort")

    def sort(self, arr: List[int]) -> Tuple[List[int], int, int]:
        if not arr:
            return arr, 0, 0

        n = len(arr)
        comparisons = 0
        swaps = 0  

        min_val = arr[0]
        max_val = arr[0]
        
        
        for i in range(1, n):
            comparisons += 1
            if arr[i] < min_val:
                min_val = arr[i]
            else:
                comparisons += 1
                if arr[i] > max_val:
                    max_val = arr[i]

        span = max_val - min_val
        if span > 100000:
            raise ValueError(f"Span {span} exceeds the maximum allowed limit of 100,000.")

        offset = -min_val
        count = [0] * (span + 1)
        
        for val in arr:
            count[val + offset] += 1

        index = 0
        for i in range(len(count)):
            while count[i] > 0:
                arr[index] = i - offset
                index += 1
                count[i] -= 1

        return arr, comparisons, swaps

    def get_time_complexity(self) -> Dict[str, str]:
        return {
            "best": "O(n + k)",
            "average": "O(n + k)",
            "worst": "O(n + k)"
        }

    def get_space_complexity(self) -> str:
        return "O(k)"