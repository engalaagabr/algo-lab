import type { AlgorithmMetadata } from '../api/client'

interface SelectedAlgorithmsProps {
  algorithms: AlgorithmMetadata[]
  selected: string[]
}

export function SelectedAlgorithms({ algorithms, selected }: SelectedAlgorithmsProps) {
  const name = (id: string) => algorithms.find((item) => item.id === id)?.name ?? id

  return (
    <div className="controls__wide">
      <span className="controls__heading">Algorithms</span>
      {selected.length ? (
        <div className="racers" aria-label="Selected algorithms">
          {selected.map((id) => (
            <span key={id} className="racer">
              {name(id)}
            </span>
          ))}
        </div>
      ) : (
        <p className="empty">Select algorithms in Race above.</p>
      )}
    </div>
  )
}
