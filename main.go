package main

import (
	"bytes"
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"

	"github.com/go-telegram/bot"
	"github.com/go-telegram/bot/models"
	"github.com/joho/godotenv"
)

func main() {
	log.SetFlags(log.LstdFlags | log.Lshortfile)
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

	var err error

	sendErr := func(err error) {
		b.SendMessage(ctx, &bot.SendMessageParams{
			ChatID: update.Message.Chat.ID,
			Text:   err.Error(),
		})
	}

	sendMsg := func(text string) {
		b.SendMessage(ctx, &bot.SendMessageParams{
			ChatID: update.Message.Chat.ID,
			Text:   text,
		})
	}

	if strings.Contains(update.Message.Text, "tiktok") {

		// v := data.Scope.Detail.ItemInfo.ItemStruct.Video
		tikTokDown := TikTokDown{}

		link, ok := tikTokDown.ParseTikTokLink(update.Message.Text)
		if !ok {
			fmt.Println(err)
			sendErr(err)
			return
		}
		defer tikTokDown.ctx_cancel()

		sendMsg("Идёт скачивание видео, ожидайте")
		if err := tikTokDown.download(link, "video.mp4"); err != nil {
			// fmt.Println(err.Error())
			log.Default().Print(err)
			sendErr(err)
			return
			// panic(err)
		}

		fileData, errReadFile := os.ReadFile("./video.mp4")
		if errReadFile != nil {
			fmt.Println(err)
			sendErr(err)
			return
		}

		_, err = b.SendVideo(ctx, &bot.SendVideoParams{
			ChatID: update.Message.Chat.ID,
			Video:  &models.InputFileUpload{Filename: "video.mp4", Data: bytes.NewReader(fileData)},
		})
		if err != nil {
			fmt.Println(err)
			sendErr(err)
			return
		}

		_, err = b.SendMessage(ctx, &bot.SendMessageParams{
			ChatID: update.Message.Chat.ID,
			Text:   "Видео успешно загужено",
		})
		if err != nil {
			fmt.Println(err)
			sendErr(err)
			return
		}

	} else {
		_, err = b.SendMessage(ctx, &bot.SendMessageParams{
			ChatID: update.Message.Chat.ID,
			Text:   "это не ссылка на тикток видео",
		})
		if err != nil {
			fmt.Println(err)
			sendErr(err)
			return
		}
	}
}
