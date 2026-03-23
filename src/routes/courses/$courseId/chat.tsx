import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/courses/$courseId/chat')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/courses/$courseId/chat"!</div>
}
