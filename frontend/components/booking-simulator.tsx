'use client'

import { useState } from 'react'
import { useSWRConfig } from 'swr'
import { FlaskConical } from 'lucide-react'

type Result = { success: boolean; message: string } | null

export function BookingSimulator() {
  const { mutate } = useSWRConfig()
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<Result>(null)

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    setSubmitting(true)
    setResult(null)
    try {
      // Same shape Retell sends for a custom function call
      const res = await fetch('/api/retell/book-appointment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'book_appointment',
          call: { call_id: 'dashboard-test' },
          args: {
            patient_name: form.get('patient_name'),
            phone: form.get('phone'),
            email: form.get('email') || null,
            service: form.get('service'),
            date: form.get('date'),
            time: form.get('time'),
            notes: 'Booked from dashboard test panel',
          },
        }),
      })
      const data = await res.json()
      setResult({ success: Boolean(data.success), message: data.message })
      mutate('/api/appointments')
    } catch {
      setResult({ success: false, message: 'Request failed. Is the backend running?' })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section aria-label="Test booking" className="rounded-xl border border-border bg-card">
      <div className="flex items-center gap-2 border-b border-border px-5 py-4">
        <FlaskConical className="size-4 text-primary" aria-hidden="true" />
        <h2 className="font-semibold">Test the booking function</h2>
      </div>
      <form onSubmit={onSubmit} className="flex flex-col gap-3 p-5">
        <p className="text-sm text-muted-foreground">
          Sends the exact payload Retell&apos;s book_appointment custom function sends.
        </p>
        <div className="flex flex-col gap-1">
          <label htmlFor="patient_name" className="text-sm font-medium">Patient name</label>
          <input id="patient_name" name="patient_name" required defaultValue="Priya Sharma"
            className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary" />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="phone" className="text-sm font-medium">Phone</label>
          <input id="phone" name="phone" required defaultValue="+91 98765 43210"
            className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary" />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="email" className="text-sm font-medium">Email (optional)</label>
          <input id="email" name="email" type="email" placeholder="priya@example.com"
            className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary" />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="service" className="text-sm font-medium">Service</label>
          <select id="service" name="service" defaultValue="Dental Cleaning"
            className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary">
            <option>Dental Cleaning</option>
            <option>Root Canal Treatment</option>
            <option>Teeth Whitening</option>
            <option>Braces Consultation</option>
            <option>Tooth Extraction</option>
            <option>General Dental Consultation</option>
          </select>
        </div>
        <div className="flex gap-3">
          <div className="flex flex-1 flex-col gap-1">
            <label htmlFor="date" className="text-sm font-medium">Date</label>
            <input id="date" name="date" type="date" required
              className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary" />
          </div>
          <div className="flex flex-1 flex-col gap-1">
            <label htmlFor="time" className="text-sm font-medium">Time</label>
            <input id="time" name="time" type="time" required defaultValue="10:00"
              className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary" />
          </div>
        </div>
        <button type="submit" disabled={submitting}
          className="mt-1 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground disabled:opacity-60">
          {submitting ? 'Booking…' : 'Book test appointment'}
        </button>
        {result && (
          <p role="status"
            className={`rounded-lg px-3 py-2 text-sm ${result.success ? 'bg-success-muted text-success' : 'bg-destructive-muted text-destructive'}`}>
            {result.message}
          </p>
        )}
      </form>
    </section>
  )
}
