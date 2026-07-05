'use client'

import useSWR from 'swr'
import { fetcher } from '@/lib/fetcher'

type Service = { id: string; name: string; duration_min: number; fee_inr: number }
type Faq = { question: string; answer: string }

export function KnowledgeBase() {
  const { data } = useSWR('/api/clinic', fetcher)
  const services: Service[] = data?.services ?? []
  const faqs: Faq[] = data?.faqs ?? []

  return (
    <section aria-label="Agent knowledge base" className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div className="rounded-xl border border-border bg-card">
        <div className="border-b border-border px-5 py-4">
          <h2 className="font-semibold">Services the agent can book</h2>
        </div>
        <ul className="divide-y divide-border">
          {services.map((s) => (
            <li key={s.id} className="flex items-center justify-between gap-3 px-5 py-3">
              <div>
                <p className="text-sm font-medium">{s.name}</p>
                <p className="text-xs text-muted-foreground">{s.duration_min} min slot</p>
              </div>
              <span className="font-mono text-sm">₹{s.fee_inr.toLocaleString('en-IN')}</span>
            </li>
          ))}
          {services.length === 0 && (
            <li className="px-5 py-8 text-center text-sm text-muted-foreground">Loading services…</li>
          )}
        </ul>
      </div>
      <div className="rounded-xl border border-border bg-card">
        <div className="border-b border-border px-5 py-4">
          <h2 className="font-semibold">FAQ knowledge base</h2>
        </div>
        <ul className="divide-y divide-border">
          {faqs.map((f) => (
            <li key={f.question} className="px-5 py-3">
              <p className="text-sm font-medium">{f.question}</p>
              <p className="mt-0.5 text-sm leading-relaxed text-muted-foreground">{f.answer}</p>
            </li>
          ))}
          {faqs.length === 0 && (
            <li className="px-5 py-8 text-center text-sm text-muted-foreground">Loading FAQs…</li>
          )}
        </ul>
      </div>
    </section>
  )
}
