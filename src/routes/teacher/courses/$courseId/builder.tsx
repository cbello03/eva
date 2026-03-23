import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/teacher/courses/$courseId/builder')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/teacher/courses/$courseId/builder"!</div>
}
