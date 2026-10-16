from base import SortingAlgorithm
from typing import List, Dict, Tuple

class HeapSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("Heap sort")

    def sort(self, arr: List[int]) -> Tuple[List[int], int, int]:
        n = len(arr)
        comparisons = 0
        swaps = 0

        def heapify(n: int, i: int):
            nonlocal comparisons, swaps
            largest = i
            left = 2 * i + 1
            right = 2 * i + 2

            # مقارنة العنصر الأيسر
            if left < n:
                comparisons += 1
                if arr[left] > arr[largest]:
                    largest = left

            # مقارنة العنصر الأيمن
            if right < n:
                comparisons += 1
                if arr[right] > arr[largest]:
                    largest = right

            # لو الـ largest اتغير، هنعمل تبديل ونكمل الـ heapify
            if largest != i:
                arr[i], arr[largest] = arr[largest], arr[i]
                swaps += 1
                heapify(n, largest)

        # بناء الـ Max Heap
        for i in range(n // 2 - 1, -1, -1):
            heapify(n, i)

        # سحب العناصر واحد بواحد من الهيب
        for i in range(n - 1, 0, -1):
            arr[i], arr[0] = arr[0], arr[i]
            swaps += 1
            heapify(i, 0)

        return arr, comparisons, swaps

    def get_time_complexity(self) -> Dict[str, str]:
        return {
            "best": "O(n log n)",
            "average": "O(n log n)",
            "worst": "O(n log n)"
        }

    def get_space_complexity(self) -> str:
        return "O(1)"