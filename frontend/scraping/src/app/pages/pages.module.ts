import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { DashboardComponent } from './dashboard/dashboard.component';
import { MonitoreoComponent } from './monitoreo/monitoreo.component';



@NgModule({
  declarations: [
    DashboardComponent,
    MonitoreoComponent
  ],
  imports: [
    CommonModule,
    RouterModule
  ],
  exports: [
    RouterModule
  ]
})
export class PagesModule { }
