import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NavComponent } from './nav/nav.component';
import { SidenavComponent } from './sidenav/sidenav.component';
import { RouterModule } from '@angular/router';



@NgModule({
  declarations: [
    NavComponent,
    SidenavComponent
  ],
  imports: [
    CommonModule,
    RouterModule
],
  exports: [
    SidenavComponent,
    NavComponent
  ]
})
export class LayoutsModule { }
