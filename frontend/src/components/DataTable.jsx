export default function DataTable({ records }) {
  if (!records || records.length === 0) return null

  // Flatten nested objects for display
  const flatRecords = records.map(r => {
    const flat = {}
    for (const [k, v] of Object.entries(r)) {
      flat[k] = typeof v === 'object' && v !== null ? JSON.stringify(v) : String(v ?? '')
    }
    return flat
  })

  const columns = [...new Set(flatRecords.flatMap(r => Object.keys(r)))]

  return (
    <div className="data-table-wrap">
      <div className="data-table-label" style={{ padding: '8px 12px 0' }}>
        {records.length} record{records.length !== 1 ? 's' : ''} extracted
      </div>
      <table className="data-table">
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {flatRecords.map((row, i) => (
            <tr key={i}>
              {columns.map(col => (
                <td key={col} title={row[col] || ''}>
                  {row[col] || '—'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
