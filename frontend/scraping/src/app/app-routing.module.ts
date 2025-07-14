import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SidenavComponent } from './Layouts/sidenav/sidenav.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { MonitoreoComponent } from './pages/monitoreo/monitoreo.component';

const routes: Routes = [
  {
    path: '',
    component: SidenavComponent, // <--- contiene el sidenav
    children: [
      { path: '', component: DashboardComponent },
      { path: 'monitoreo', component: MonitoreoComponent },
      // { path: 'alertas', component: AlertasComponent },
      // ...
    ],
  },
  { path: '**', redirectTo: '' },
];


@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
