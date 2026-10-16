import type { AlgorithmMetadata } from '../api/client'
import { formatCount } from './lab'

interface AlgorithmPickerProps {
  algorithms: AlgorithmMetadata[]
  selected: string[]
  onChange: (selected: string[]) => void
  max: number
  /** Largest input the run will use; algorithms with a lower size cap are disabled. */
  inputSize?: number
}

export function AlgorithmPicker({ algorithms, selected, onChange, max, inputSize = 0 }: AlgorithmPickerProps) {
  const toggle = (id: string) =>
    onChange(selected.includes(id) ? selected.filter((item) => item !== id) : [...selected, id])

  return (
    <>
      <h2>
        Algorithms <small>up to {max}</small>
      </h2>
      <ul className="setup__algorithms">
        {algorithms.map((algorithm) => {
          const checked = selected.includes(algorithm.id)
          const tooLarge = inputSize > algorithm.max_size
          const disabled = !checked && (selected.length >= max || tooLarge)
          return (
            <li key={algorithm.id}>
              <label className={tooLarge ? 'is-limited' : undefined}>
                <input type="checkbox" checked={checked} disabled={disabled} onChange={() => toggle(algorithm.id)} />
                <span>
                  {algorithm.name}
                  {tooLarge && <small> max {formatCount(algorithm.max_size)} values</small>}
                </span>
              </label>
            </li>
          )
        })}
      </ul>
    </>
  )
}
