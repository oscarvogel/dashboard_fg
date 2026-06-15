// Verificar datos que retorna cada endpoint
// Ejecutar esto en la consola del navegador

async function verificarEndpoints() {
  const auth_token = localStorage.getItem('access_token')
  const headers = { 'Authorization': `Bearer ${auth_token}` }
  
  // Test para mayo de 2026, unidad 1 (COSECHA FULL TREE)
  const params = {
    month: 5,
    year: 2026,
    cod_un: 1
  }
  
  console.log('=== Verificando /api/produccion-ejecutiva/ ===')
  const respEjecutiva = await fetch(
    `/api/produccion-ejecutiva/?month=${params.month}&year=${params.year}&cod_un=${params.cod_un}`,
    { headers }
  ).then(r => r.json())
  
  console.log('produccion_esperada_acumulada:', respEjecutiva.produccion_esperada_acumulada)
  console.log('unidad_produccion:', respEjecutiva.unidad_produccion)
  console.log('registros count:', respEjecutiva.registros?.length || 0)
  
  // Calcular total producción
  const totalProd = respEjecutiva.registros?.reduce((sum, r) => sum + (parseFloat(r.produccion) || 0), 0) || 0
  console.log('total produccion (from registros):', totalProd)
  console.log('eficiencia calculada:', ((totalProd / respEjecutiva.produccion_esperada_acumulada) * 100).toFixed(2))
  
  // Test para dashboard (rango de fechas equivalente a todo el mes)
  const startDate = '2026-05-01'
  const endDate = '2026-05-31'
  
  console.log('\n=== Verificando /api/produccion-dashboard/ (rango completo mayo) ===')
  const respDashboard = await fetch(
    `/api/produccion-dashboard/?start_date=${startDate}&end_date=${endDate}&cod_un=1`,
    { headers }
  ).then(r => r.json())
  
  console.log('produccion_esperada_acumulada:', respDashboard.produccion_esperada_acumulada)
  console.log('unidad_produccion:', respDashboard.unidad_produccion)
  console.log('results count:', respDashboard.results?.length || 0)
  
  // Calcular total producción desde results
  const totalProdDash = respDashboard.results?.reduce((sum, r) => sum + (parseFloat(r.produccion) || 0), 0) || 0
  console.log('total produccion (from results):', totalProdDash)
  console.log('eficiencia calculada:', ((totalProdDash / respDashboard.produccion_esperada_acumulada) * 100).toFixed(2))
}

// Ejecutar
verificarEndpoints().catch(console.error)
