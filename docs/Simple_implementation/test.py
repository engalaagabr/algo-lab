from Algorithms.bubble import BubbleSort
from Algorithms.selection  import SelectionSort
from Algorithms.insertion  import InsertionSort
from Algorithms.binary_insertion import BinaryInsertionSort
from Algorithms.counting import CountingSort
from Algorithms.quick import QuickSort
from Algorithms.heap import HeapSort
from Algorithms.shell import ShellSort

def run_all_tests():
    
    test_data = [64, 34, 25, 12, 22, 11, 90, -5, 8]
    
    
    algorithms = [
        BubbleSort(),
        SelectionSort(),
        InsertionSort(),
        BinaryInsertionSort(),
        CountingSort(),
        QuickSort(),
        HeapSort(),
        ShellSort()
    ]
    
    print(f"Original Data: {test_data}\n" + "="*50)
    
    for algo in algorithms:
    
        arr_copy = test_data.copy()
        
        try:
            
            sorted_arr, comps, swaps = algo.sort(arr_copy)
            
            print(f"Algorithm: {algo.name}")
            print(f"Sorted:    {sorted_arr}")
            print(f"Stats:     Comparisons = {comps}, Swaps/Operations = {swaps}")
            print(f"Complexity: {algo.get_time_complexity()}")
            print("-" * 50)
            
        except Exception as e:
            print(f"Algorithm: {algo.name} -> Error: {e}")
            print("-" * 50)

if __name__ == "__main__":
    run_all_tests()