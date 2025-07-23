import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { DashboardComponent } from './dashboard/dashboard.component';
import { MonitoreoComponent } from './monitoreo/monitoreo.component';
import { FormsModule } from '@angular/forms';
import { NgChartsModule } from 'ng2-charts';



@NgModule({
  declarations: [
    DashboardComponent,
    MonitoreoComponent
  ],
  imports: [
    CommonModule,
    NgChartsModule,
    RouterModule,
    FormsModule,
  ],
  exports: [
    RouterModule
  ]
})
export class PagesModule { }
