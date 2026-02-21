import Link from "next/link";

export default function HomePage() {
  return (
    <main className="container mx-auto p-6">
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Bem-vindo ao VokeTag
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          Sistema completo de autenticação de produtos com tecnologia NFC. 
          Proteja sua marca e garanta a autenticidade dos seus produtos.
        </p>
        
        <div className="grid gap-6 md:grid-cols-3 max-w-4xl mx-auto mb-12">
          <Link href="/scan" className="card hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="p-3 bg-blue-100 rounded-full w-12 h-12 mx-auto mb-4 flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Escanear Produto</h3>
              <p className="text-gray-600">Verifique a autenticidade de produtos usando tags NFC</p>
            </div>
          </Link>

          <Link href="/products" className="card hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="p-3 bg-green-100 rounded-full w-12 h-12 mx-auto mb-4 flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Gerenciar Produtos</h3>
              <p className="text-gray-600">Cadastre e gerencie produtos no sistema</p>
            </div>
          </Link>

          <Link href="/dashboard" className="card hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="p-3 bg-purple-100 rounded-full w-12 h-12 mx-auto mb-4 flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Dashboard</h3>
              <p className="text-gray-600">Visualize estatísticas e relatórios do sistema</p>
            </div>
          </Link>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 max-w-2xl mx-auto">
          <h2 className="text-lg font-semibold text-blue-900 mb-2">Status do Sistema</h2>
          <div className="flex items-center justify-center space-x-6 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-blue-800">Scan Service</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-blue-800">Factory Service</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-blue-800">Admin Service</span>
            </div>
          </div>
          <p className="text-blue-700 mt-2">Todos os serviços estão funcionando normalmente</p>
        </div>
      </div>
    </main>
  );
}