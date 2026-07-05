import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import './globals.css'

const _geist = Geist({ subsets: ['latin'] })
const _geistMono = Geist_Mono({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AI Receptionist Dashboard | QuensultingAI Dental Clinic',
  description:
    'Admin dashboard for the RetellAI voice receptionist: appointments, call logs, FAQ knowledge base, and integration status.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="bg-background">
      <body className="font-sans text-foreground antialiased">{children}</body>
    </html>
  )
}
