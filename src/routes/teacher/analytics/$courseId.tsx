import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/teacher/analytics/$courseId')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/teacher/analytics/$courseId"!</div>
}
