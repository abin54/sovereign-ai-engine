import Redis from 'ioredis';

export class MessageBus {
  private redis: Redis;

  constructor(host = 'localhost', port = 6379) {
    this.redis = new Redis({ host, port });
  }

  async publish(topic: string, message: any) {
    const data = JSON.stringify(message);
    await this.redis.xadd(topic, '*', 'data', data);
  }

  async subscribe(topic: string, group: string, consumer: string, callback: (msg: any) => void) {
    try {
      await this.redis.xgroup('CREATE', topic, group, '0', 'MKSTREAM');
    } catch (err: any) {
      if (!err.message.includes('BUSYGROUP')) throw err;
    }

    while (true) {
      const results = await this.redis.xreadgroup('GROUP', group, consumer, 'BLOCK', 1000, 'COUNT', 1, 'STREAMS', topic, '>');
      if (results) {
        for (const [topicName, messages] of results) {
          for (const [id, [_, data]] of messages) {
            callback(JSON.parse(data as string));
            await this.redis.xack(topic, group, id);
          }
        }
      }
    }
  }
}
