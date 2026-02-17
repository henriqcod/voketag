package events

import (
	"context"
	"fmt"
	"time"

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
	
	// HIGH SECURITY FIX: Properly check error from Publish()
	// Publish() returns a *PublishResult which must be awaited
	result := p.topic.Publish(ctx, msg)
	
	// Wait for publish to complete with timeout
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	
	serverID, err := result.Get(ctx)
	if err != nil {
		return fmt.Errorf("failed to publish scan event for tag_id=%s: %w", tagID.String(), err)
	}
	
	// Successfully published, serverID is the message ID from Pub/Sub
	_ = serverID
	return nil
}
