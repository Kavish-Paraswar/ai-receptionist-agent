'use client'

import useSWR from 'swr'
import { fetcher, formatDateTime } from '@/lib/fetcher'

type CallLog = {
  id: number
  call_id: string | null
  caller_number: string | null
  event: string
  summary: string | null
  sentiment: string | null
  created_at: string
}

const eventStyles: Record<string, string> = {
  call_started: 'bg-muted text-muted-foreground',
  call_ended: 'bg-accent-muted text-accent',
  call_analyzed: 'bg-success-muted text-success',
}

export function CallLogsTable() {
  const { data, isLoading } = useSWR('/api/call-logs', fetcher, { refreshInterval: 10000 })
  const logs: CallLog[] = data?.call_logs ?? []

  return (
    <section aria-label="Call logs" className="rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border px-5 py-4">
        <h2 className="font-semibold">Call activity</h2>
        <span className="text-sm text-muted-foreground">Retell webhook events</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted-foreground">
              <th scope="col" className="px-5 py-3 font-medium">Event</th>
              <th scope="col" className="px-5 py-3 font-medium">Caller</th>
              <th scope="col" className="px-5 py-3 font-medium">Summary</th>
              <th scope="col" className="px-5 py-3 font-medium">Received</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 && (
              <tr>
                <td colSpan={4} className="px-5 py-10 text-center text-muted-foreground">
                  {isLoading
                    ? 'Loading call logs…'
                    : 'No call events yet. Point your Retell agent webhook at /api/retell/webhook.'}
                </td>
              </tr>
            )}
            {logs.map((log) => (
              <tr key={log.id} className="border-b border-border last:border-0">
                <td className="px-5 py-3">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${eventStyles[log.event] ?? 'bg-muted text-muted-foreground'}`}
                  >
                    {log.event}
                  </span>
                </td>
                <td className="px-5 py-3 font-mono text-xs">{log.caller_number ?? '—'}</td>
                <td className="max-w-xs px-5 py-3">
                  <p className="truncate" title={log.summary ?? undefined}>
                    {log.summary ?? '—'}
                  </p>
                  {log.sentiment && (
                    <p className="text-xs text-muted-foreground">Sentiment: {log.sentiment}</p>
                  )}
                </td>
                <td className="px-5 py-3 text-muted-foreground">{formatDateTime(log.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
