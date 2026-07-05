'use client'

import useSWR from 'swr'
import { Stethoscope } from 'lucide-react'
import { fetcher } from '@/lib/fetcher'

export function DashboardHeader() {
  const { data } = useSWR('/api/health', fetcher, { refreshInterval: 15000 })
  const online = data?.status === 'ok'

  return (
    <header className="border-b border-border bg-card">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-4 md:px-6">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Stethoscope className="size-5" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-lg font-semibold leading-tight text-balance">
              QuensultingAI Dental Clinic
            </h1>
            <p className="text-sm text-muted-foreground">AI Receptionist — Admin Dashboard</p>
          </div>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-border px-3 py-1.5">
          <span
            className={`size-2 rounded-full ${online ? 'bg-success' : 'bg-destructive'}`}
            aria-hidden="true"
          />
          <span className="text-sm font-medium">
            {online ? 'Agent backend online' : 'Backend offline'}
          </span>
        </div>
      </div>
    </header>
  )
}
