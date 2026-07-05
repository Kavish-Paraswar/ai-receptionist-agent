'use client'

import useSWR from 'swr'
import { fetcher, formatDateTime } from '@/lib/fetcher'

type Appointment = {
  appointment_id: string
  patient_name: string
  phone: string
  email: string | null
  service: string
  appointment_time: string
  status: string
  created_at: string
}

export function AppointmentsTable() {
  const { data, isLoading } = useSWR('/api/appointments', fetcher, { refreshInterval: 10000 })
  const appointments: Appointment[] = data?.appointments ?? []

  return (
    <section aria-label="Appointments" className="rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border px-5 py-4">
        <h2 className="font-semibold">Appointments</h2>
        <span className="text-sm text-muted-foreground">
          Booked by the voice agent, synced to Google Sheets
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted-foreground">
              <th scope="col" className="px-5 py-3 font-medium">Booking ID</th>
              <th scope="col" className="px-5 py-3 font-medium">Patient</th>
              <th scope="col" className="px-5 py-3 font-medium">Service</th>
              <th scope="col" className="px-5 py-3 font-medium">Scheduled for</th>
              <th scope="col" className="px-5 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {appointments.length === 0 && (
              <tr>
                <td colSpan={5} className="px-5 py-10 text-center text-muted-foreground">
                  {isLoading
                    ? 'Loading appointments…'
                    : 'No appointments yet. Use the test booking panel or call the agent to create one.'}
                </td>
              </tr>
            )}
            {appointments.map((a) => (
              <tr key={a.appointment_id} className="border-b border-border last:border-0">
                <td className="px-5 py-3 font-mono text-xs">{a.appointment_id}</td>
                <td className="px-5 py-3">
                  <p className="font-medium">{a.patient_name}</p>
                  <p className="text-xs text-muted-foreground">{a.phone}</p>
                </td>
                <td className="px-5 py-3">{a.service}</td>
                <td className="px-5 py-3">{formatDateTime(a.appointment_time)}</td>
                <td className="px-5 py-3">
                  <span className="inline-flex items-center rounded-full bg-success-muted px-2.5 py-0.5 text-xs font-medium text-success">
                    {a.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
