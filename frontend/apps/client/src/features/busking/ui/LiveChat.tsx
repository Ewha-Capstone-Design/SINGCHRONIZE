'use client';

import { useState, useRef, useEffect } from 'react';
import type { ChatMessageType } from '@/entities/busking/model/types';
import { InputField } from '@singchronize/ui';

const LiveChat = ({ messages }: { messages: ChatMessageType[] }) => {
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className='p-6 pt-8 flex flex-col gap-8 h-full bg-gray-900'>
      <h3 className='typo-24b text-white shrink-0'>라이브 채팅</h3>

      <div className='flex-1 flex flex-col gap-3 overflow-y-auto scrollbar-hide'>
        {messages.map((msg) => (
          <div key={msg.id} className='flex flex-col gap-2'>
            <div className='flex items-center gap-1'>
              <div className='size-5.5 rounded-full bg-gray-600 shrink-0 overflow-hidden'>
                {msg.profileImage && (
                  <img
                    src={msg.profileImage}
                    alt={msg.username}
                    className='size-full object-cover'
                  />
                )}
              </div>
              <span className='typo-12r text-gray-200'>{msg.username}</span>
            </div>
            <div className='px-4 py-3 rounded-20 bg-gray-800'>
              <p className='typo-14r text-white'>{msg.message}</p>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <InputField
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder='채팅을 입력하세요'
      />
    </div>
  );
};

export default LiveChat;
