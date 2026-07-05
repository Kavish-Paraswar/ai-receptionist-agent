'use client'

import useSWR from 'swr'
import { CalendarCheck, PhoneCall, Table2, Mail } from 'lucide-react'
import { fetcher } from '@/lib/fetcher'

export function StatCards() {
  const { data: appts } = useSWR('/api/appointments', fetcher, { refreshInterval: 10000 })
  const { data: calls } = useSWR('/api/call-logs', fetcher, { refreshInterval: 10000 })
  const { data: integrations } = useSWR('/api/integrations', fetcher, { refreshInterval: 30000 })

  const appointments = appts?.appointments ?? []
  const today = new Date().toISOString().slice(0, 10)
  const todayCount = appointments.filter((a: { appointment_time: string }) =>
    a.appointment_time?.startsWith(today),
  ).length
  const uniqueCalls = new Set(
    (calls?.call_logs ?? []).map((c: { call_id: string | null }) => c.call_id).filter(Boolean),
  ).size

  const sheets = integrations?.google_sheets
  const notif = integrations?.notifications

  const cards = [
    {
      label: 'Appointments booked',
      value: String(appointments.length),
      sub: `${todayCount} scheduled today`,
      icon: CalendarCheck,
    },
    {
      label: 'Calls handled',
      value: String(uniqueCalls),
      sub: `${calls?.call_logs?.length ?? 0} webhook events`,
      icon: PhoneCall,
    },
    {
      label: 'Google Sheets sync',
      value: sheets?.connected ? 'Connected' : sheets?.configured ? 'Error' : 'Not set',
      sub: sheets?.connected ? 'Rows mirrored live' : 'SQLite fallback active',
      icon: Table2,
    },
    {
      label: 'Confirmations',
      value:
        notif?.email_configured || notif?.webhook_configured ? 'Enabled' : 'Not set',
      sub: [
        notif?.email_configured ? 'Email' : null,
        notif?.webhook_configured ? 'Webhook' : null,
      ]
        .filter(Boolean)
        .join(' + ') || 'Add SMTP or webhook env vars',
      icon: Mail,
    },
  ]

  return (
    <section aria-label="Key metrics" className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="flex items-start justify-between gap-3 rounded-xl border border-border bg-card p-5"
        >
          <div className="flex flex-col gap-1">
            <p className="text-sm text-muted-foreground">{card.label}</p>
            <p className="text-2xl font-semibold tracking-tight">{card.value}</p>
            <p className="text-xs text-muted-foreground">{card.sub}</p>
          </div>
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-muted text-primary">
            <card.icon className="size-4" aria-hidden="true" />
          </div>
        </div>
      ))}
    </section>
  )
}
