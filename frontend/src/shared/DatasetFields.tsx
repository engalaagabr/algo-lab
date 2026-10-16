import { useText } from '../i18n/language'
import { DISTRIBUTIONS, integerText, type DatasetSettings, type Distribution } from './lab'

interface DatasetFieldsProps {
  value: DatasetSettings
  onChange: (value: DatasetSettings) => void
  maxSize: number
  /** Slider suits small visual arrays; a number field suits benchmark sizes. */
  sizeControl: 'slider' | 'number'
}

export function DatasetFields({ value, onChange, maxSize, sizeControl }: DatasetFieldsProps) {
  const text = useText()
  const set = <K extends keyof DatasetSettings>(key: K, next: DatasetSettings[K]) =>
    onChange({ ...value, [key]: next })

  return (
    <>
      <label>
        <span className="controls__label">
          {text.size} {sizeControl === 'slider' && <output>{value.size}</output>}
        </span>
        {sizeControl === 'slider' ? (
          <input type="range" min={2} max={maxSize} value={value.size} onChange={(event) => set('size', Number(event.target.value))} />
        ) : (
          <input
            type="number"
            min={1}
            max={maxSize}
            value={value.size}
            onChange={(event) => set('size', Math.max(1, Math.min(maxSize, Number(event.target.value) || 1)))}
          />
        )}
      </label>
      <div className="controls__row">
        <label>
          {text.min}
          <input type="number" value={value.minimum} onChange={(event) => set('minimum', Number(event.target.value))} />
        </label>
        <label>
          {text.max}
          <input type="number" value={value.maximum} onChange={(event) => set('maximum', Number(event.target.value))} />
        </label>
      </div>
      <label>
        {text.pattern}
        <select value={value.distribution} onChange={(event) => set('distribution', event.target.value as Distribution)}>
          {DISTRIBUTIONS.map((item) => (
            <option key={item.value} value={item.value}>
              {text[item.label]}
            </option>
          ))}
        </select>
      </label>
      <label>
        {text.seed}
        <input value={value.seed} placeholder={text.seedPlaceholder} inputMode="numeric" onChange={(event) => set('seed', integerText(event.target.value, false))} />
      </label>
    </>
  )
}
