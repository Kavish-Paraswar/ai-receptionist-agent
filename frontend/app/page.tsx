import { DashboardHeader } from '@/components/dashboard-header'
import { StatCards } from '@/components/stat-cards'
import { AppointmentsTable } from '@/components/appointments-table'
import { CallLogsTable } from '@/components/call-logs-table'
import { KnowledgeBase } from '@/components/knowledge-base'
import { IntegrationsPanel } from '@/components/integrations-panel'
import { BookingSimulator } from '@/components/booking-simulator'

export default function Page() {
  return (
    <div className="min-h-screen">
      <DashboardHeader />
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-8 md:px-6">
        <StatCards />
        <div className="flex flex-col gap-6 lg:flex-row">
          <div className="flex min-w-0 flex-1 flex-col gap-6">
            <AppointmentsTable />
            <CallLogsTable />
          </div>
          <div className="flex w-full flex-col gap-6 lg:w-96">
            <BookingSimulator />
            <IntegrationsPanel />
          </div>
        </div>
        <KnowledgeBase />
      </main>
      <footer className="border-t border-border py-6">
        <p className="text-center text-sm text-muted-foreground">
          QuensultingAI Dental Clinic — AI Voice Receptionist built with RetellAI Conversational Flow + FastAPI
        </p>
      </footer>
    </div>
  )
}
