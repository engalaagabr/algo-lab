import type { AlgorithmMetadata } from '../api/client'

interface AlgorithmSelectionProps {
  algorithms: AlgorithmMetadata[]
  selected: string[]
  onChange: (selected: string[]) => void
  max?: number
}

export function AlgorithmSelection({ algorithms, selected, onChange, max = 10 }: AlgorithmSelectionProps) {
  const available = algorithms.filter((algorithm) => !selected.includes(algorithm.id))
  const remove = (id: string) => onChange(selected.filter((item) => item !== id))
  const add = (id: string) => {
    if (id && !selected.includes(id) && selected.length < max) onChange([...selected, id])
  }

  return (
    <div className="controls__wide">
      <span className="controls__heading">
        Algorithms <small>up to {max}</small>
      </span>
      <div className="racers">
        {selected.map((id) => {
          const name = algorithms.find((algorithm) => algorithm.id === id)?.name ?? id
          return (
            <span key={id} className="racer">
              {name}
              <button type="button" aria-label={`Remove ${name}`} onClick={() => remove(id)}>
                ×
              </button>
            </span>
          )
        })}
        {available.length > 0 && selected.length < max && (
          <select
            className="racers__add"
            value=""
            aria-label="Add algorithm"
            onChange={(event) => add(event.target.value)}
          >
            <option value="">+ Add algorithm</option>
            {available.map((algorithm) => (
              <option key={algorithm.id} value={algorithm.id}>
                {algorithm.name}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  )
}
