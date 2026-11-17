package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"

	"github.com/go-telegram/bot"
	"github.com/go-telegram/bot/models"
	"github.com/joho/godotenv"
)

func main() {
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt)
	defer cancel()

	if err := godotenv.Load(); err != nil {
		fmt.Println("No .env file found")
	}

	TOKEN, exists := os.LookupEnv("TOKEN")
	if !exists {
		panic("environment TOKEN not found")
	}

	opts := []bot.Option{
		bot.WithDefaultHandler(handler),
	}

	b, err := bot.New(TOKEN, opts...)
	if err != nil {
		panic("error run bot")
	}

	b.Start(ctx)
}

func handler(ctx context.Context, b *bot.Bot, update *models.Update) {
	b.SendVideo(ctx, &bot.SendVideoParams{
		ChatID: update.Message.Chat.ID,
		Video:  &models.InputFileString{Data: "video.mp4"},
	})
	b.SendMessage(ctx, &bot.SendMessageParams{
		ChatID: update.Message.Chat.ID,
		Text:   update.Message.Text,
	})
}
