import type { AlgorithmMetadata } from '../api/client'
import { useText } from '../i18n/language'
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
  const text = useText()
  const toggle = (id: string) =>
    onChange(selected.includes(id) ? selected.filter((item) => item !== id) : [...selected, id])

  return (
    <div className="controls__wide">
      <span className="controls__heading">
        {text.algorithms} <small>{text.upTo(max)}</small>
      </span>
      <div className="chips">
        {algorithms.map((algorithm) => {
          const checked = selected.includes(algorithm.id)
          const tooLarge = inputSize > algorithm.max_size
          return (
            <button
              key={algorithm.id}
              type="button"
              className="chip"
              aria-pressed={checked}
              disabled={!checked && (selected.length >= max || tooLarge)}
              onClick={() => toggle(algorithm.id)}
            >
              {algorithm.name}
              {tooLarge && <small>{text.maxValues(formatCount(algorithm.max_size))}</small>}
            </button>
          )
        })}
      </div>
    </div>
  )
}
