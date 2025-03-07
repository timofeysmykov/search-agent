import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function POST(req: Request) {
  try {
    const data = await req.json();
    const enabled = !!data.enabled;
    
    // В реальном приложении здесь можно было бы сохранять значение 
    // в базу данных или другое постоянное хранилище
    
    // Для демонстрации обновляем переменную окружения TEST_MODE
    // Важно: в продакшен-окружении это не будет работать, так как .env.local 
    // загружается только при старте приложения
    process.env.TEST_MODE = enabled ? 'true' : 'false';
    
    const message = `Тестовый режим ${enabled ? 'включен' : 'выключен'}`;
    console.log(message);
    
    return NextResponse.json({
      test_mode: enabled,
      message: message
    }, { status: 200 });
  } catch (error) {
    console.error('Ошибка при переключении тестового режима:', error);
    
    return NextResponse.json({ 
      error: 'Ошибка при переключении тестового режима',
      test_mode: process.env.TEST_MODE === 'true'
    }, { status: 500 });
  }
}
