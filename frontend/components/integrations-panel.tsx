'use client'

import useSWR from 'swr'
import { CheckCircle2, CircleAlert, CircleDashed } from 'lucide-react'
import { fetcher } from '@/lib/fetcher'

function StatusRow({
  label,
  state,
  detail,
}: {
  label: string
  state: 'ok' | 'error' | 'unset'
  detail: string
}) {
  const Icon = state === 'ok' ? CheckCircle2 : state === 'error' ? CircleAlert : CircleDashed
  const color =
    state === 'ok' ? 'text-success' : state === 'error' ? 'text-destructive' : 'text-muted-foreground'
  return (
    <li className="flex items-start gap-3 py-3">
      <Icon className={`mt-0.5 size-4 shrink-0 ${color}`} aria-hidden="true" />
      <div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{detail}</p>
      </div>
    </li>
  )
}

export function IntegrationsPanel() {
  const { data } = useSWR('/api/integrations', fetcher, { refreshInterval: 30000 })
  const sheets = data?.google_sheets
  const notif = data?.notifications

  return (
    <section aria-label="Integration status" className="rounded-xl border border-border bg-card">
      <div className="border-b border-border px-5 py-4">
        <h2 className="font-semibold">Integrations</h2>
      </div>
      <ul className="divide-y divide-border px-5">
        <StatusRow
          label="SQLite store"
          state="ok"
          detail="Always on — powers this dashboard with zero setup."
        />
        <StatusRow
          label="Google Sheets"
          state={sheets?.connected ? 'ok' : sheets?.configured ? 'error' : 'unset'}
          detail={
            sheets?.connected
              ? 'Appointments and call logs mirrored to your sheet.'
              : sheets?.configured
                ? `Configured but failing: ${sheets?.error ?? 'unknown error'}`
                : 'Set GOOGLE_SERVICE_ACCOUNT_JSON and GOOGLE_SHEET_ID to enable.'
          }
        />
        <StatusRow
          label="Confirmation email (SMTP)"
          state={notif?.email_configured ? 'ok' : 'unset'}
          detail={
            notif?.email_configured
              ? 'Booking confirmations sent to the caller.'
              : 'Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD to enable.'
          }
        />
        <StatusRow
          label="Confirmation webhook"
          state={notif?.webhook_configured ? 'ok' : 'unset'}
          detail={
            notif?.webhook_configured
              ? 'appointment.confirmed events fired after each booking.'
              : 'Set CONFIRMATION_WEBHOOK_URL to enable.'
          }
        />
      </ul>
    </section>
  )
}
