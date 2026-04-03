import { RouterProvider, createRouter } from '@tanstack/react-router';
import { Providers } from './providers';

// Importamos el árbol autogenerado por el plugin
import { routeTree } from '../routeTree.gen';

// Creamos el router
const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

export function App() {
  return (
    <Providers>
      <RouterProvider router={router} />
    </Providers>
  );
}