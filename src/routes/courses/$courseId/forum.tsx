import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/courses/$courseId/forum')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/courses/$courseId/forum"!</div>
}
