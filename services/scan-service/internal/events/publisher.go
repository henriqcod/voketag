package events

import (
	"context"

	"cloud.google.com/go/pubsub"
	"github.com/google/uuid"
)

type Publisher struct {
	client *pubsub.Client
	topic  *pubsub.Topic
}

func NewPublisher(projectID, topicID string) (*Publisher, error) {
	ctx := context.Background()
	client, err := pubsub.NewClient(ctx, projectID)
	if err != nil {
		return nil, err
	}
	topic := client.Topic(topicID)
	return &Publisher{client: client, topic: topic}, nil
}

func (p *Publisher) PublishScanEvent(ctx context.Context, tagID uuid.UUID, event []byte) error {
	msg := &pubsub.Message{
		Data: event,
		Attributes: map[string]string{
			"tag_id": tagID.String(),
		},
	}
	_ = p.topic.Publish(ctx, msg)
	return nil
}
