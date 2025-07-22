import { Component, OnInit, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { ComentarioService, Comentario } from '../../services/comentario/comentario.service';
import { ChartConfiguration, ChartType } from 'chart.js';
import { Chart } from 'chart.js';
import { Inject, PLATFORM_ID } from '@angular/core';



@Component({
  selector: 'app-dashboard',
  standalone: false,
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit, AfterViewInit {
  comentarios: Comentario[] = [];
  private graficoClasificacion?: Chart;
  private graficoToxicidad?: Chart;

  filtroNivel: string = '';
  filtroClasificacion: string = '';
  comentariosFiltrados: Comentario[] = [];

  plataformas: string[] = [];
  clasificacionesPorPlataforma: Record<string, { insulto: number; otro: number }> = {};
  graficosPorPlataforma: { plataforma: string; labels: string[]; data: number[] }[] = [];



  // Estadísticas principales
  totalComentarios = 0;
  totalToxicos = 0;
  alertasCriticas = 0;
  precisionIA = 0;

  // Datos para secciones nuevas
  conteoPorPlataforma: Record<string, number> = {};
  conteoPorClasificacion: Record<string, number> = {};
  conteoPorNivel: Record<string, number> = {};
  palabrasClaveMasComunes: string[] = [];

  alertasRecientes: Comentario[] = [];

  clasificacionesKeys: string[] = [];
  nivelesToxicidadKeys: string[] = [];

  toxicidadChartLabels: string[] = ['bajo', 'medio', 'alto'];
  toxicidadChartData: ChartConfiguration<'bar'>['data']['datasets'] = [
    { data: [0, 0, 0], label: 'Comentarios por nivel de toxicidad' }
  ];

  clasificacionesChartLabels: string[] = [];
  clasificacionesChartData: ChartConfiguration<'bar'>['data']['datasets'] = [];

  nivelesChartLabels: string[] = [];
  nivelesChartData: ChartConfiguration<'bar'>['data']['datasets'] = [];

  chartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    plugins: {
      legend: { display: true }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: { display: true, text: 'Cantidad de comentarios' }
      },
      x: {
        title: { display: true, text: 'Categoría' }
      }
    }
  };

  @ViewChild('graficoClasificacion', { static: false }) canvasRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('graficoNivelToxicidad', { static: false }) graficoNivelRef!: ElementRef<HTMLCanvasElement>;

  private canvasListo = false;

  constructor(
    private comentarioService: ComentarioService,
    @Inject(PLATFORM_ID) private platformId: Object
  ) { }


  ngOnInit(): void {
    // this.actualizarDashboard();
    this.actualizarDashboard()
  }

  private dashboardInicializado = false;

  ngAfterViewInit(): void {
    if (!this.dashboardInicializado) {
      this.canvasListo = true;
      this.dashboardInicializado = true;

      // Dale al DOM tiempo para terminar de renderizar los <canvas>
      setTimeout(() => {
        this.actualizarDashboard();
      }, 0);
    }
  }

  filtrarComentarios(): void {
    this.comentariosFiltrados = this.comentarios.filter(comentario => {
      const coincideNivel = this.filtroNivel === '' || comentario.nivel_toxicidad === this.filtroNivel;
      const coincideClasificacion = this.filtroClasificacion === '' || comentario.clasificacion === this.filtroClasificacion;
      return coincideNivel && coincideClasificacion;
    });
  }

  actualizarDashboard(): void {
    this.resetearEstadisticas();

    this.comentarioService.getComentarios().subscribe({
      next: (comentarios: Comentario[]) => {
        this.comentarios = comentarios;
        this.totalComentarios = comentarios.length;

        let totalProbabilidad = 0;
        const palabrasContadas: Record<string, number> = {};

        comentarios.forEach((c) => {
          totalProbabilidad += c.probabilidad_toxicidad;

          if (c.nivel_toxicidad === 'alto') this.totalToxicos++;

          if (c.clasificacion === 'insulto' && c.probabilidad_toxicidad > 0.9) {
            this.alertasCriticas++;
          }

          this.conteoPorClasificacion[c.clasificacion] =
            (this.conteoPorClasificacion[c.clasificacion] || 0) + 1;

          this.conteoPorNivel[c.nivel_toxicidad] =
            (this.conteoPorNivel[c.nivel_toxicidad] || 0) + 1;

          this.conteoPorPlataforma[c.plataforma] =
            (this.conteoPorPlataforma[c.plataforma] || 0) + 1;

          if (Array.isArray(c.palabras_clave)) {
            for (const palabra of c.palabras_clave) {
              const clave = palabra.toLowerCase();
              palabrasContadas[clave] = (palabrasContadas[clave] || 0) + 1;
            }
          }
        });

        this.precisionIA = comentarios.length > 0
          ? +(totalProbabilidad / comentarios.length * 100).toFixed(1)
          : 0;

        this.palabrasClaveMasComunes = Object.entries(palabrasContadas)
          .sort(([, a], [, b]) => b - a)
          .slice(0, 10)
          .map(([palabra]) => palabra);

        this.clasificacionesKeys = Object.keys(this.conteoPorClasificacion);
        this.nivelesToxicidadKeys = Object.keys(this.conteoPorNivel);

        this.alertasRecientes = comentarios
          .filter(c => c.nivel_toxicidad === 'alto')
          .sort((a, b) => +new Date(b.fecha) - +new Date(a.fecha))
          .slice(0, 5);

        this.toxicidadChartData = [
          {
            data: [
              this.conteoPorNivel['bajo'] || 0,
              this.conteoPorNivel['medio'] || 0,
              this.conteoPorNivel['alto'] || 0
            ],
            label: 'Comentarios por nivel de toxicidad'
          }
        ];

        this.clasificacionesChartLabels = this.clasificacionesKeys;
        this.clasificacionesChartData = [
          {
            data: this.clasificacionesKeys.map(k => this.conteoPorClasificacion[k]),
            label: 'Clasificación de Comentarios'
          }
        ];

        this.nivelesChartLabels = this.nivelesToxicidadKeys;
        this.nivelesChartData = [
          {
            data: this.nivelesToxicidadKeys.map(k => this.conteoPorNivel[k]),
            label: 'Nivel de Toxicidad'
          }
        ];

        // Renderizar gráfico personalizado si el canvas ya está listo
        setTimeout(() => {
          this.crearGraficoClasificacion();
          this.crearGraficoNivelToxicidad();
        }, 0);

        this.comentariosFiltrados = [...comentarios];

        this.clasificacionesPorPlataforma = {};

        for (const comentario of this.comentarios) {
          const plataforma = comentario.plataforma.toLowerCase();
          const clasificacion = comentario.clasificacion.toLowerCase();

          if (!this.clasificacionesPorPlataforma[plataforma]) {
            this.clasificacionesPorPlataforma[plataforma] = { insulto: 0, otro: 0 };
          }

          if (clasificacion === 'insulto') {
            this.clasificacionesPorPlataforma[plataforma].insulto++;
          } else {
            this.clasificacionesPorPlataforma[plataforma].otro++;
          }
        }

        this.plataformas = Object.keys(this.clasificacionesPorPlataforma);

        // Para generar los datos del gráfico
        this.graficosPorPlataforma = this.plataformas.map((plataforma) => {
          const datos = this.clasificacionesPorPlataforma[plataforma];
          return {
            plataforma,
            labels: ['Insulto', 'Otro'],
            data: [datos.insulto, datos.otro],
          };
        });

      },
      error: (error) => {
        console.error('Error al cargar los comentarios:', error);
      }
    });
  }

  private resetearEstadisticas(): void {
    this.comentarios = [];
    this.totalComentarios = 0;
    this.totalToxicos = 0;
    this.alertasCriticas = 0;
    this.precisionIA = 0;
    this.alertasRecientes = [];

    this.conteoPorPlataforma = {};
    this.conteoPorClasificacion = {};
    this.conteoPorNivel = {};
    this.palabrasClaveMasComunes = [];

    this.clasificacionesKeys = [];
    this.nivelesToxicidadKeys = [];

    this.clasificacionesChartLabels = [];
    this.clasificacionesChartData = [];

    this.nivelesChartLabels = [];
    this.nivelesChartData = [];

    this.toxicidadChartData = [
      { data: [0, 0, 0], label: 'Comentarios por nivel de toxicidad' }
    ];
  }

  mostrarEnConsola(): void {
    console.log(this.comentarios);
  }


  crearGraficoClasificacion(): void {
    if (typeof window === 'undefined') return;
    if (!this.canvasListo || !this.canvasRef?.nativeElement) return;

    if (this.graficoClasificacion) {
      this.graficoClasificacion.destroy();
    }

    const canvas = this.canvasRef.nativeElement;
    const data = this.clasificacionesKeys.map(k => this.conteoPorClasificacion[k]);
    const labels = this.clasificacionesKeys;

    this.graficoClasificacion = new Chart(canvas, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Distribución por Clasificación',
          data,
          backgroundColor: [
            'rgba(54, 162, 235, 0.5)',
            'rgba(255, 206, 86, 0.5)',
            'rgba(255, 99, 132, 0.5)'
          ],
          borderColor: [
            'rgba(54, 162, 235, 1)',
            'rgba(255, 206, 86, 1)',
            'rgba(255, 99, 132, 1)'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true }
        },
        scales: {
          y: { beginAtZero: true },
          x: {
            title: { display: true, text: 'Clasificación' }
          }
        }
      }
    });
  }

  crearGraficoNivelToxicidad(): void {
    if (typeof window === 'undefined') return;
    if (!this.canvasListo || !this.graficoNivelRef?.nativeElement) return;

    if (this.graficoToxicidad) {
      this.graficoToxicidad.destroy();
    }

    const canvas = this.graficoNivelRef.nativeElement;
    const data = [
      this.conteoPorNivel['bajo'] || 0,
      this.conteoPorNivel['medio'] || 0,
      this.conteoPorNivel['alto'] || 0
    ];

    const labels = ['bajo', 'medio', 'alto'];

    this.graficoToxicidad = new Chart(canvas, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Distribución por Nivel de Toxicidad',
          data,
          backgroundColor: [
            'rgba(75, 192, 192, 0.5)',
            'rgba(255, 206, 86, 0.5)',
            'rgba(255, 99, 132, 0.5)'
          ],
          borderColor: [
            'rgba(75, 192, 192, 1)',
            'rgba(255, 206, 86, 1)',
            'rgba(255, 99, 132, 1)'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true }
        },
        scales: {
          y: { beginAtZero: true },
          x: {
            title: { display: true, text: 'Nivel de Toxicidad' }
          }
        }
      }
    });
  }
}
